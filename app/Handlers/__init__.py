from aiogram import Router

from .about import router_about
from .basket import router_basket
from .catalog import router_catalog
from .registration import router_register
from .user import router_user
from .support import router_support
from .payment import router_payment
from .admin import router_admin

full_router = [router_register,
               router_user,
               router_catalog,
               router_about,
               router_basket,
                router_support,
               router_payment,
               router_admin,
               ]

main_router = Router()
main_router.include_routers(*full_router)
