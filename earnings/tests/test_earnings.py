from earnings import earnings


def test_2_earnings():
    df = earnings.get_df_one_date("2021-04-30")
    assert df.shape[0] == 2


def test_0_earnings():
    df = earnings._get_df_for_date_and_offset("2021-04-30", 100)
    assert df.shape[0] == 0


def test_161_earnings():
    df = earnings.get_df_one_date("2021-04-27")
    assert df.shape[0] == 161
