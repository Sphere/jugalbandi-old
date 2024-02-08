import time
from datetime import datetime, timedelta

import extra_streamlit_components as stx
import httpx
import streamlit as st
from helper import (
    InputValidator,
    generate_api_key,
    get_hashed_password,
    token_decode,
    token_encode,
    verify_password,
)
from tenant_repository import TenantRepository

state = st.session_state
st.set_page_config(page_title="Jugalbandi", page_icon="😎", layout="centered")
cookie_manager = stx.CookieManager()
validator = InputValidator()
tenant_repository = TenantRepository()


def init_state():
    if "email" not in state:
        state["email"] = ""
    if "password" not in state:
        state["password"] = ""
    if "authentication_status" not in state:
        state["authentication_status"] = None
    if "logout" not in state:
        state["logout"] = None
    if "uuid_number" not in state:
        state["uuid_number"] = ""
    if "name" not in state:
        state["name"] = ""
    if "reg_email" not in state:
        state["reg_email"] = ""
    if "reg_password" not in state:
        state["reg_password"] = ""
    if "confirm_password" not in state:
        state["confirm_password"] = ""
    if "login_button_option" not in state:
        state["login_button_option"] = True
    if "login_button_type" not in state:
        state["login_button_type"] = "primary"
    if "signup_button_option" not in state:
        state["signup_button_option"] = False
    if "signup_button_type" not in state:
        state["signup_button_type"] = "secondary"


def _check_cookie():
    token = cookie_manager.get("Some cookie name")
    if token is not None:
        token = token_decode(token)
        if token is not False:
            print("INSIDE TOKEN")
            print(token)
            if not state["logout"]:
                if token["exp_date"] > datetime.utcnow().timestamp():
                    if "email" in token:
                        state["email"] = token["email"]
                        state["authentication_status"] = True


def _set_state_cb(**kwargs):
    for state_key, widget_key in kwargs.items():
        val = state.get(widget_key, None)
        if val is not None or val == "":
            setattr(state, state_key, state[widget_key])


def _set_login_cb(email, password):
    if login(email, password):
        expiry_date_time = datetime.now() + timedelta(days=30.0)
        expiry_date = expiry_date_time.timestamp()
        token = token_encode(expiry_date, email)
        cookie_manager.set(
            "Some cookie name",
            token,
            expires_at=expiry_date_time,
        )
        state["authentication_status"] = True
        state["logout"] = False


def login(email, password):
    print("INSIDE LOGIN")
    try:
        if not validator.validate_input_for_length(email):
            raise Exception("Email should not be empty")
        if not validator.validate_input_for_length(password):
            raise Exception("Password should not be empty")
        tenant_detail = tenant_repository.get_tenant_details(email)
        if tenant_detail is None:
            raise Exception("Invalid login credentials")
        else:
            return verify_password(password, tenant_detail[-1])
    except Exception as e:
        st.error(e, icon="🚨")


def logout():
    print("INSIDE LOGOUT")
    cookie_manager.delete("Some cookie name")
    print("BEFORE", cookie_manager.get(cookie="Some cookie name"))
    if "Some cookie name" in cookie_manager.cookies:
        del cookie_manager.cookies["Some cookie name"]
    print("AFTER", cookie_manager.get(cookie="Some cookie name"))
    state["logout"] = True
    state["email"] = None
    state["password"] = None
    state["authentication_status"] = None


def is_login_option():
    state["login_button_option"] = True
    state["signup_button_option"] = False
    state["login_button_type"] = "primary"
    state["signup_button_type"] = "secondary"


def is_signup_option():
    state["signup_button_option"] = True
    state["login_button_option"] = False
    state["signup_button_type"] = "primary"
    state["login_button_type"] = "secondary"


def _set_signup_cb(name, email, reg_password, confirm_password):
    try:
        if not validator.validate_input_for_length(name):
            raise Exception("Name should not be empty")
        if not validator.validate_input_for_length(email):
            raise Exception("Email should not be empty")
        if not validator.validate_email(email):
            raise Exception("Email is not valid")
        registered_emails = tenant_repository.get_all_tenant_emails()
        if email in registered_emails:
            raise Exception("Email is already registered")
        if not validator.validate_input_for_length(
            reg_password
        ) or not validator.validate_input_for_length(confirm_password):
            raise Exception("Password/confirm password fields cannot be empty")
        if reg_password != confirm_password:
            raise Exception("Passwords do not match")
        print("Inside Signup")
        with st.spinner("Registration in progress...."):
            tenant_repository.insert_into_tenant(
                name=name,
                email_id=email,
                api_key=generate_api_key(),
                password=get_hashed_password(password=reg_password),
            )
        print("Insertion complete")
        st.toast("Registration successful", icon="✅")
        time.sleep(1)
        is_login_option()
    except Exception as e:
        st.error(e, icon="🚨")


def main():
    init_state()
    st.title("Jugalbandi :sunglasses:")
    if not state["authentication_status"]:
        _check_cookie()
        if not state["authentication_status"]:
            st.subheader("Choose an action")
            login_column, signup_column = st.columns(2)
            login_column.button(
                label="Login", on_click=is_login_option, type=state["login_button_type"]
            )
            if state["login_button_option"]:
                st.text_input(
                    "Email:",
                    value=state.email,
                    key="email_input",
                    on_change=_set_state_cb,
                    kwargs={"email": "email_input"},
                )
                st.text_input(
                    "Password:",
                    type="password",
                    value=state.password,
                    key="password_input",
                    on_change=_set_state_cb,
                    kwargs={"password": "password_input"},
                )
                _, column_two, _ = st.columns(3)
                with column_two:
                    st.button(
                        label="Submit",
                        key="login_submit",
                        on_click=_set_login_cb,
                        args=(state.email, state.password),
                    )

            signup_column.button(
                label="Sign up",
                on_click=is_signup_option,
                type=state["signup_button_type"],
            )
            if state["signup_button_option"]:
                st.text_input(
                    "Name:",
                    value=state.name,
                    key="name_input",
                    on_change=_set_state_cb,
                    kwargs={"name": "name_input"},
                )
                st.text_input(
                    "Email:",
                    value=state.reg_email,
                    key="reg_email_input",
                    on_change=_set_state_cb,
                    kwargs={"reg_email": "reg_email_input"},
                )
                st.text_input(
                    "Password:",
                    type="password",
                    value=state.reg_password,
                    key="reg_password_input",
                    on_change=_set_state_cb,
                    kwargs={"reg_password": "reg_password_input"},
                )
                st.text_input(
                    "Confirm password:",
                    type="password",
                    value=state.confirm_password,
                    key="confirm_password_input",
                    on_change=_set_state_cb,
                    kwargs={"confirm_password": "confirm_password_input"},
                )
                _, column_two, _ = st.columns(3)
                with column_two:
                    st.button(
                        label="Submit",
                        key="signup_submit",
                        on_click=_set_signup_cb,
                        args=(
                            state.name,
                            state.reg_email,
                            state.reg_password,
                            state.confirm_password,
                        ),
                    )

    if state["authentication_status"] is True:
        st.title("Upload your files")
        uploaded_files = st.file_uploader(
            label="Files Upload", accept_multiple_files=True
        )
        url = "http://127.0.0.1:8000/upload-files"
        files = []
        for uploaded_file in uploaded_files:
            files.append(("files", uploaded_file))
        if len(files) > 0:
            response = httpx.post(url=url, files=files, timeout=60)
            response = response.json()
            state["uuid_number"] = response["uuid_number"]
            st.header(f"Your UUID number is {state['uuid_number']}")
        _, column_two, _ = st.columns(3)
        with column_two:
            st.button(label="Logout", on_click=logout)


if __name__ == "__main__":
    main()