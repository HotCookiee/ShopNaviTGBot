from aiogram import Router
from Handlers.registration import router_register
from Handlers.user import router_user

main_router = Router()


main_router.include_router(router_register)
main_router.include_router(router_user)

