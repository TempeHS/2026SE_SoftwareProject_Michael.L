def test_validate_signup_input_valid(app_module):
    err = app_module.validate_signup_input(
        "Michael Smith", "michael@example.com", "StrongPass123!"
    )
    assert err is None


def test_validate_signup_input_bad_password(app_module):
    err = app_module.validate_signup_input(
        "Michael Smith", "michael@example.com", "weakpass"
    )
    assert err is not None


def test_is_safe_next(app_module):
    assert app_module.is_safe_next("/your-huddle") is True
    assert app_module.is_safe_next("https://evil.com") is False
    assert app_module.is_safe_next("//evil.com") is False


def test_generate_invite_code(app_module):
    code = app_module.generate_invite_code()
    assert len(code) == 6
    assert all(c in app_module.INVITE_CODE_ALPHABET for c in code)
