from recsys.data.preprocessing import encode_ids, k_core_filter
from recsys.data.splitting import temporal_user_split
from recsys.schema import TIMESTAMP, USER_IDX


def test_split_is_temporal_and_covers_every_user(raw_reviews):
    encoded, _, _ = encode_ids(k_core_filter(raw_reviews, k=5))
    train, val, test = temporal_user_split(encoded, val_ratio=0.2, test_ratio=0.2)

    assert len(train) + len(val) + len(test) == len(encoded)
    for split in (train, val, test):
        assert set(split[USER_IDX]) == set(encoded[USER_IDX])

    last_train = train.groupby(USER_IDX)[TIMESTAMP].max()
    first_val = val.groupby(USER_IDX)[TIMESTAMP].min()
    last_val = val.groupby(USER_IDX)[TIMESTAMP].max()
    first_test = test.groupby(USER_IDX)[TIMESTAMP].min()
    assert (last_train < first_val).all()
    assert (last_val < first_test).all()
