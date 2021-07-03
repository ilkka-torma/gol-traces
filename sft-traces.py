import time, collections


def valid_block(top_row, mid_row, bot_row, pos):
    """
        Is the 3x3 pattern at a given position of a 3-row rectangle valid?
        I.e. does it map to 0 in GoL?
    """
    mid_cell = mid_row[pos+1]
    ring_sum = sum(top_row[pos:pos+3]) + mid_row[pos] + mid_row[pos+2] + sum(bot_row[pos:pos+3])
    if mid_cell:
        return ring_sum < 2 or ring_sum > 3
    else:
        return ring_sum != 3

def iter_allowed_prefix(top_row, bot_row, prefix, end_period=False):
    """
        Iterate over locally legal words that fit to the bottom of the given rectangle and begin
	with the given prefix of length 2. If end_period is true, require further that the entire
	pattern can be continued to the right with period 3.
    """
    assert len(prefix) == 2
    length = len(top_row)
    assert 2 <= length == len(bot_row)
    if length == 2:
        yield prefix
    else:
        # Recursively pick a word of length one less and extend in both ways
        for word in iter_allowed_prefix(top_row[:-1], bot_row[:-1], prefix, end_period=False):
            for sym in range(2):
                new_row = word + (sym,)
                if end_period:
                    top_per = top_row + top_row[-3:-1]
                    bot_per = bot_row + bot_row[-3:-1]
                    new_per = new_row + new_row[-3:-1]
                    if all(valid_block(top_per, bot_per, new_per, length-i-1) for i in range(3)):
                        yield new_row
                elif valid_block(top_row, bot_row, new_row, length-3):
                    yield new_row

def encode_bin(word):
    """
        Encode a binary vector into an integer.
    """
    return sum(a * 2**i for (i,a) in enumerate(word))

def decode_bin(num, n):
    """
        Decode an integer into a pair of length-n binary tuples.
    """
    ret = []
    for _ in range(2*n):
        ret.append(num%2)
        num = num // 2
    return tuple(ret[:n]), tuple(ret[n:])

def right_trace_aut(radius, end_period=False):
    """
        NFA for one-sided vertical trace of width 2 and given right radius, possibly with periodic
        end. Alphabet is binary tuples of length 2, transitions go southward. States are
        rectangular patterns of height 2 and width radius+2, compressed into bytestrings.
        Return also C, the amount of extension needed to guarantee a word to be infinitely extendable.
    """
    alph = [(0,0),(0,1),(1,0),(1,1)]
    width = radius + 2
    trans_dict = {}
    states = set(range(2**(width*2)))
    byte_width = (width*2 + 7) // 8

    # Construct transitions
    for label in states:
        for sym in alph:
            res = []
            top_row, bot_row = decode_bin(label, width)
            for word in iter_allowed_prefix(top_row, bot_row, sym, end_period=end_period):
                res.append(encode_bin(bot_row + word))
            trans_dict[(label, sym)] = res

    # Remove states that lead to dead ends or can't be reached after some number of steps, compute C
    pad_needed = 0
    while True:
        new_states = set(st2
                         for st in states
                         for sym in alph
                         for st2 in trans_dict[(st, sym)])
        new_states = set(st
                         for st in new_states
                         if any(st2 in states
                                for sym in alph
                                for st2 in trans_dict[(st, sym)]))
        if new_states == states:
            break
        states = new_states
        pad_needed += 1

    # Update transition dict based on removed states, encode states as byte vectors
    trans_dict = {(st.to_bytes(byte_width, byteorder='big'),
                   sym)
                  :
                  [st2.to_bytes(byte_width, byteorder='big')
                   for st2 in trans_dict[(st, sym)]
                   if st2 in states]
                  for (st, sym) in trans_dict
                  if st in states}
    
    return (trans_dict, [st.to_bytes(byte_width, byteorder='big') for st in states], pad_needed)

def determinize(trans_dict, states, alph):
    """
        Determinize a given NFA using the powerset construction.
        It is assumed that all its states are initial and final.
    """

    # Maintain sets of seen and unprocessed state sets, and integer labels for seen sets
    init_st = frozenset(states)
    seen = {init_st : 0}
    finals = set([0])
    frontier = collections.deque([(init_st, 0)])

    det_trans = {}
    num_seen = 1

    while frontier:
        # Pick an unprocessed state set, go over its successors
        st_set, st_num = frontier.pop()
        for sym in alph:
            new_st_set = frozenset(st2 for st in st_set for st2 in trans_dict[(st, sym)])
            if new_st_set in seen:
                new_num = seen[new_st_set]
            else:
                # Pick a new label for the set
                new_num = num_seen
                num_seen += 1
                frontier.append((new_st_set, new_num))
                seen[new_st_set] = new_num
                # All nonempty sets of states are final
                if new_st_set:
                    finals.add(new_num)
            # Transitions are stored using the integer labels
            det_trans[(st_num, sym)] = new_num

    return det_trans, set(range(num_seen)), 0, finals
    
def minimize(trans_dict, states, init_st, final_states, alph):
    """
        Minimize a DFA using Moore's algorithm.
        It is assumed that all states are reachable.
    """

    # Maintain a coloring of the states; states with different colors are provably non-equivalent
    coloring = {}
    colors = set()
    for st in states:
        if st in final_states:
            coloring[st] = 1
            colors.add(1)
        else:
            coloring[st] = 0
            colors.add(0)
    num_colors = len(colors)

    # Iteratively update coloring based on the colors of successors
    while True:
        # First, use tuples of colors as new colors
        new_coloring = {}
        new_colors = set()
        for st in states:
            new_color = (coloring[st],) + tuple(coloring[trans_dict[(st, sym)]] for sym in alph)
            new_coloring[st] = new_color
            new_colors.add(new_color)
        # Then, encode new colors as integers
        color_nums = { color : i for (i, color) in enumerate(new_colors) }
        new_coloring = { st : color_nums[color] for (st, color) in new_coloring.items() }
        new_num_colors = len(new_colors)
        # If strictly more colors were needed, repeat
        if num_colors == new_num_colors:
            break
        else:
            colors = new_colors
            coloring = new_coloring
            num_colors = new_num_colors

    # Compute new transition function and state set
    new_trans_dict = {}
    for st in states:
        for sym in alph:
            new_trans_dict[(new_coloring[st], sym)] = new_coloring[trans_dict[(st, sym)]]
    
    new_final_states = set(new_coloring[st] for st in final_states)
    return new_trans_dict, set(new_coloring.values()), new_coloring[init_st], new_final_states
            

def diff_nonempty(dict_A, init_A, sink_A, dict_B, states_B, alph, track=False, verbose=False):
    """
        Is A\B nonempty for DFA A and NFA B?
        If track is True, return shortest word in A\B or None.
        If track is False, return True/False.
        Assumes A has a unique nonfinal state, which is a sink.
        Assumes all states of B are initial and final, and labeled by bytestrings.
        To preserve memory, states are stored in a compressed form.
    """

    # Compress states for a slight decrease in memory use
    def compre(x,y):
        return (x, b"".join(sorted(y)))

    clock = time.perf_counter()

    # Keep track of (compressed) processed states of pair automaton, B is implicitly determinized
    inits_B = frozenset(states_B)
    frontier = set([(init_A, inits_B, compre(init_A, inits_B))])
    if not track:
        reachables = set(c for (_,_,c) in frontier)
    else:
        reachables = {c : [] for (_,_,c) in frontier}

    # Process all reachable pairs in depth-first order, stopping if A accepts but B does not
    i = 0
    while frontier:
        i += 1
        if verbose:print("{}: {} states processed in {:.3f} seconds.".format(i,
			len(reachables), time.perf_counter()-clock))
        newfrontier = set()
       
        for (st_A, set_B, compr) in frontier:
            for sym in alph:
                new_A = dict_A[(st_A, sym)]
                if new_A == sink_A:
                    # We can forget the sink state of A
                    continue
                news_B = frozenset(st for sts in set_B for st in dict_B[(sts, sym)])
                if not news_B:
                    # A accepts but B does not: A\B is nonempty
                    if track:
                        return reachables[compr] + [sym]
                    else:
                        return True
                new_c = compre(new_A, news_B)
                if new_c in reachables:
                    continue
                if not track:
                    reachables.add(new_c)
                else:
                    reachables[new_c] = reachables[compr] + [sym]
                newfrontier.add((new_A, news_B, new_c))
        frontier = newfrontier
    return False

def verify_results():
    alph = [(0,0),(0,1),(1,0),(1,1)]
    clock = time.perf_counter()
    t4_dict, t4_states, t4_C = right_trace_aut(4)
    t4d_dict, t4d_states, t4d_init, t4d_finals = determinize(t4_dict, t4_states, alph)
    t4m_dict, t4m_states, t4m_init, t4m_finals = minimize(t4d_dict,
		t4d_states, t4d_init, t4d_finals, alph)
    t4m_sink = (t4m_states - t4m_finals).pop()
    print("Constructed minimal radius-4 trace automaton, took {:.3f} seconds.".format(
		time.perf_counter()-clock))
    print("For this trace, C is {}.".format(t4_C))
    clock = time.perf_counter()
    t6p_dict, t6p_states, _ = right_trace_aut(6, end_period=True)
    print("Constructed 3-periodic radius-6 trace automaton, took {:.3f} seconds.".format(
                time.perf_counter()-clock))
    clock = time.perf_counter()
    if diff_nonempty(t4m_dict, t4m_init, t4m_sink, t6p_dict, t6p_states, alph, verbose=True):
        print("Trace not periodizable at distance 6, took {:.3f} seconds.".format(
	            time.perf_counter()-clock))
    else:
        print("Trace is periodizable at distance 6, took {:.3f} seconds.".format(
	            time.perf_counter()-clock))

if __name__ == "__main__":
    verify_results()
