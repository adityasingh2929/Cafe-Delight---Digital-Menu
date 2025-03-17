from django.contrib import admin
from .models import Cart,Order,OTP,CartItem,Category,CustomUser,MenuItem,OrderItem
# Register your models here.


admin.site.register(Category)
admin.site.register(MenuItem)
admin.site.register(CartItem)
admin.site.register(Cart)
admin.site.register(OTP)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(CustomUser)