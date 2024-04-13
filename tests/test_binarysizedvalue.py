import pytest

from kaso_mashin.common.base_types import BinarySizedValue, BinaryScale


def test_binarysizedvalue():
    expected = 1
    upper_base = BinarySizedValue(value=expected, scale=BinaryScale.E)
    for scale in [BinaryScale.P, BinaryScale.T, BinaryScale.G, BinaryScale.M, BinaryScale.k, BinaryScale.b]:
        expected = expected * 1024
        assert upper_base.at_scale(scale) == BinarySizedValue(value=expected, scale=scale)

    expected = 1152921504606846976
    lower_base = BinarySizedValue(value=expected, scale=BinaryScale.b)
    for scale in [BinaryScale.k, BinaryScale.M, BinaryScale.G, BinaryScale.T, BinaryScale.P]:
        expected = expected / 1024
        assert lower_base.at_scale(scale) == BinarySizedValue(value=expected, scale=scale)
