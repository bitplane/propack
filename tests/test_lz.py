from propack.lz import _find_best_match


def test_match_search_stops_when_remaining_input_is_matched():
    class CountedData:
        reads = 0

        def __getitem__(self, index):
            self.reads += 1
            assert self.reads < 10000, "search kept comparing after finding a complete suffix match"
            return ord("A")

    data = CountedData()
    assert _find_best_match(data, 8193, 12288, 0, 4096) == (4095, 1)
