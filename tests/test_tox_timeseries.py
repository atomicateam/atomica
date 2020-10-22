# Test timeseries utility object

import atomica as at
import numpy as np

def test_printing():
    a = at.TimeSeries([1], [5])
    print(a)


def test_equality():
    # Two time series should be equal if their values are equal
    a = at.TimeSeries()
    b = at.TimeSeries()
    assert a == b

    a.insert(None, 1)
    assert a != b

    b.insert(None, 1)
    assert a == b

    a = at.TimeSeries([1, 2, 3], [1, 2, 3])
    b = at.TimeSeries([1, 2, 3], [1, 2, 3])
    c = at.TimeSeries([1, 2, 3, 4], [1, 2, 3, 4])
    assert a == b
    assert a != c
    a.insert(None, 1)
    assert a != b


def test_constructor():
    a = at.TimeSeries()
    a.insert(1,1)
    a.insert(2,2)
    a.insert(None,0)
    a.insert(3,3)

    b = at.TimeSeries([None,1,2,3],[0,1,2,3])
    assert a == b

    c = at.TimeSeries(np.array([None,1,2,3]),np.array([0,1,2,3]))
    assert a == c

    a.insert(np.array([2,3]),[4,5])
    c.insert(2,4)
    c.insert(3,5)
    assert a == c

    d = at.TimeSeries(range(3),[0,1,4])
    assert a != d
    d.remove(0)
    d.insert(3,5)
    d.insert(None,0)
    assert a == d


def test_insert_sorting():
    a = at.TimeSeries([1,2],[1,2])

    # Insert at end
    a.insert(3,3)
    assert a.t == [1,2,3]
    assert a.vals == [1,2,3]

    # Insert in middle
    a.insert(2.5,2.5)
    assert a.t == [1,2,2.5,3]
    assert a.vals == [1,2,2.5,3]

    # Insert at start
    a.insert(0,0)
    assert a.t == [0,1,2,2.5,3]
    assert a.vals == [0,1,2,2.5,3]

    # Overwrite existing at end
    a.insert(3,4)
    assert a.t == [0,1,2,2.5,3]
    assert a.vals == [0,1,2,2.5,4]

    # Overwrite existing at start
    a.insert(0, 4)
    assert a.t == [0, 1, 2, 2.5, 3]
    assert a.vals == [4, 1, 2, 2.5, 4]

    # Overwrite existing in middle
    a.insert(1, 4)
    assert a.t == [0, 1, 2, 2.5, 3]
    assert a.vals == [4, 4, 2, 2.5, 4]


if __name__ == '__main__':

    test_constructor()
    test_printing()
    test_equality()
    test_insert_sorting()