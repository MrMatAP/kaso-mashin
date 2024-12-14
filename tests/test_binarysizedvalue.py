import kaso_mashin.base


def test_binarysizedvalue():
    expected = 1
    upper_base = kaso_mashin.base.BinarySizedValue(
        value=expected, scale=kaso_mashin.base.BinaryScale.E
    )
    for scale in [
        kaso_mashin.base.BinaryScale.P,
        kaso_mashin.base.BinaryScale.T,
        kaso_mashin.base.BinaryScale.G,
        kaso_mashin.base.BinaryScale.M,
        kaso_mashin.base.BinaryScale.k,
        kaso_mashin.base.BinaryScale.b,
    ]:
        expected = expected * 1024
        assert upper_base.at_scale(scale) == kaso_mashin.base.BinarySizedValue(
            value=expected, scale=scale
        )

    expected = 1152921504606846976
    lower_base = kaso_mashin.base.BinarySizedValue(
        value=expected, scale=kaso_mashin.base.BinaryScale.b
    )
    for scale in [
        kaso_mashin.base.BinaryScale.k,
        kaso_mashin.base.BinaryScale.M,
        kaso_mashin.base.BinaryScale.G,
        kaso_mashin.base.BinaryScale.T,
        kaso_mashin.base.BinaryScale.P,
    ]:
        expected = expected / 1024
        assert lower_base.at_scale(scale) == kaso_mashin.base.BinarySizedValue(
            value=expected, scale=scale
        )
