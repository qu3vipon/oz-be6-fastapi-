from fastapi import APIRouter, Path, Body, status, HTTPException, Depends
from fastapi.security import HTTPBasicCredentials, HTTPBasic
from sqlalchemy.orm import Session

from config.database import get_session
from user.authentication import check_password, encode_access_token, authenticate
from user.models import User
from user.request import SignUpRequestBody
from user.response import UserMeResponse, UserResponse, JWTResponse

router = APIRouter(prefix="/users", tags=["User"])


@router.post(
    "",
    response_model=UserMeResponse,
    status_code=status.HTTP_201_CREATED,
)
def sign_up_handler(
    body: SignUpRequestBody,
    session: Session = Depends(get_session),
):
    new_user = User.create(username=body.username, password=body.password)
    session.add(new_user)
    session.commit()  # db 저장

    return UserMeResponse(
        id=new_user.id, username=new_user.username, password=new_user.password
    )

@router.post(
    "/login",
    response_model=JWTResponse,
    status_code=status.HTTP_200_OK,
)
def login_handler(
    credentials: HTTPBasicCredentials = Depends(HTTPBasic()),
    session: Session = Depends(get_session),
):
    user: User | None = session.query(User).filter(
        User.username == credentials.username
    ).first()

    if user:
        if check_password(
            plain_text=credentials.password, hashed_password=user.password
        ):
            return JWTResponse(
                access_token=encode_access_token(username=user.username),
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found",
    )


# 내 정보 조회
@router.get("/me")
def get_me_handler(
    username: str = Depends(authenticate),
    session: Session = Depends(get_session),
):
    user: User | None = session.query(User).filter(User.username == username).first()

    if user:
        return UserMeResponse(
            id=user.id, username=user.username, password=user.password
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found",
    )


@router.patch(
    "/me",
    response_model=UserMeResponse,
    status_code=status.HTTP_200_OK,
)
def update_user_handler(
    username: str = Depends(authenticate),
    new_password: str = Body(..., embed=True),
    session: Session = Depends(get_session),
):
    user: User | None = session.query(User).filter(User.username == username).first()

    if user:
        user.update_password(password=new_password)
        session.add(user)
        session.commit()

        return UserMeResponse(
            id=user.id, username=user.username, password=user.password
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found",
    )

@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
def delete_user_handler(
    username: str = Depends(authenticate),
    session: Session = Depends(get_session),
):
    user: User | None = session.query(User).filter(User.username == username).first()

    if user:
        session.delete(user)
        session.commit()
        return

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found",
    )


# 다른 사람 정보를 조회하는 경우
@router.get(
    "/{username}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def get_user_handler(
    _: str = Depends(authenticate),
    username: str = Path(..., max_length=10),
    session: Session = Depends(get_session),
):
    user: User | None = session.query(User).filter(User.username == username).first()
    if user:
        return UserResponse(username=user.username)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found",
    )
