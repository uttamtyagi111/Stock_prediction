from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import razorpay
import logging
from .models import Plan, UserProfile
from razorpay.errors import BadRequestError, ServerError



logger = logging.getLogger(__name__)
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        plan_status = user_profile.check_plan_status()
        
        data = {
            'username': request.user.username,
            'email_count': user_profile.emails_sent,
            'plan_name': user_profile.plan_name,
            'plan_status': user_profile.plan_status,
            'plan_expiry_date': user_profile.plan_expiration_date
            
        }
        return Response(data, status=status.HTTP_200_OK)
    except UserProfile.DoesNotExist:
        return Response({'message': 'User profile not found.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def get_available_plans(request):
    plans = Plan.objects.all()
    data = [{'id': plan.id, 'name': plan.name, 'email_limit': plan.email_limit, 'duration_days': plan.duration_days} for plan in plans]
    return Response(data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def choose_plan_view(request):
    """
    Allows authenticated users to choose a plan.
    """
    plan_name = request.data.get('plan_name')
    
    if plan_name not in ['basic', 'premium']:
        return Response({'message': 'Invalid plan selected. Choose either "basic" or "premium".'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:

        user_profile = UserProfile.objects.get(user=request.user)
        plan = Plan.objects.get(name__iexact=plan_name)
        
        user_profile.plan_name = plan.name
        user_profile.current_plan = plan
        user_profile.plan_status = "active"
        user_profile.emails_sent = 0  
        user_profile.plan_expiration_date = timezone.now() + timedelta(days=plan.duration_days)
        user_profile.save()

        return Response({'message': f'Plan successfully updated to {plan_name}.'}, status=status.HTTP_200_OK)
    except UserProfile.DoesNotExist:
        return Response({'message': 'User profile not found.'}, status=status.HTTP_404_NOT_FOUND)
    except Plan.DoesNotExist:
        return Response({'message': 'Selected plan not found.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def upgrade_plan(request):
    """
    Allows authenticated users to upgrade to a new plan.
    """
    plan_name = request.data.get('plan_name')
    
    if plan_name not in ['basic', 'premium']:
        return Response({'message': 'Invalid plan selected. Choose either "basic" or "premium".'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user_profile = UserProfile.objects.get(user=request.user)
        new_plan = Plan.objects.get(name__iexact=plan_name)
        
        user_profile.plan_name = new_plan.name
        user_profile.current_plan = new_plan
        user_profile.plan_status = "active"
        user_profile.emails_sent = 0  # Reset email count when upgrading
        user_profile.plan_expiration_date = timezone.now() + timedelta(days=new_plan.duration_days)
        user_profile.save()
        
        return Response({'message': f'Plan successfully upgraded to {plan_name}.'}, status=status.HTTP_200_OK)
    except UserProfile.DoesNotExist:
        return Response({'message': 'User profile not found.'}, status=status.HTTP_404_NOT_FOUND)
    except Plan.DoesNotExist:
        return Response({'message': 'Selected plan not found.'}, status=status.HTTP_404_NOT_FOUND)


logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order(request):
    """
    Creates an order for the selected plan and updates the user profile with the plan details upon order creation.
    """
    plan_name = request.data.get('plan_name')
    if plan_name not in ['basic', 'premium']:
        return Response({'message': 'Invalid plan selected. Choose either "basic" or "premium".'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Fetch the selected plan from the database
        plan = Plan.objects.get(name__iexact=plan_name)

        # Calculate order amount (in paise for INR)
        order_amount = int(plan.price * 100)
        order_currency = 'INR'
        order_receipt = f'order_rcptid_{request.user.id}'

        # Initialize Razorpay client and create an order
        razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))
        razorpay_order = razorpay_client.order.create({
            'amount': order_amount,
            'currency': order_currency,
            'receipt': order_receipt,
            'payment_capture': '1'
        })

    except Plan.DoesNotExist:
        return Response({'message': 'Selected plan not found.'}, status=status.HTTP_404_NOT_FOUND)
    except BadRequestError as e:
        logger.error(f'Bad Request: {e}')
        return Response({'message': 'Error creating Razorpay order due to bad request.'}, status=status.HTTP_400_BAD_REQUEST)
    except ServerError as e:
        logger.error(f'Server Error: {e}')
        return Response({'message': 'Error creating Razorpay order due to server issue.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.error(f'Unexpected Error: {e}')
        return Response({'message': 'Error creating Razorpay order.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Fetch and update the user's profile with the plan details
        user_profile = request.user.userprofile
        user_profile.plan_name = plan.name
        user_profile.current_plan = plan
        user_profile.plan_status = "active"
        user_profile.emails_sent = 0  # Reset email count for the new plan
        user_profile.plan_expiration_date = timezone.now() + timedelta(days=plan.duration_days)
        user_profile.device_limit = plan.device_limit  # Update device limit based on the plan
        user_profile.razorpay_order_id = razorpay_order['id']
        user_profile.save()

    except UserProfile.DoesNotExist:
        return Response({'message': 'User profile not found.'}, status=status.HTTP_404_NOT_FOUND)
    
    return Response({
        'razorpay_order_id': razorpay_order['id'],
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'amount': order_amount,
        'currency': order_currency,
        'plan_name': plan.name,
        'message': f'Order created successfully for the {plan_name} plan with updated profile details.'
    }, status=status.HTTP_200_OK)



# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def create_order(request):
#     plan_name = request.data.get('plan_name')
#     if not plan_name:
#         return Response({'message': 'Plan name is required.'}, status=400)

#     try:
#         plan = Plan.objects.get(name__iexact=plan_name)
#         order_amount = int(plan.price * 100)
#         order_currency = 'INR'
#         order_receipt = f'order_rcptid_{request.user.id}'

#         razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))
#         razorpay_order = razorpay_client.order.create({
#             'amount': order_amount,
#             'currency': order_currency,
#             'receipt': order_receipt,
#             'payment_capture': '1'
#         })
        
#         # print("Razorpay Order Created:", razorpay_order)
#     except BadRequestError as e:
#         logger.error(f'Bad Request: {e}')
#         return Response({'message': 'Error creating Razorpay order due to bad request.'}, status=400)
#     except ServerError as e:
#         logger.error(f'Server Error: {e}')
#         return Response({'message': 'Error creating Razorpay order due to server issue.'}, status=500)
#     except Exception as e:
#         logger.error(f'Unexpected Error: {e}')
#         return Response({'message': 'Error creating Razorpay order.'}, status=400)

#     user_profile = request.user.userprofile
#     user_profile.razorpay_order_id = razorpay_order['id']
#     user_profile.save()

#     return Response({
#         'razorpay_order_id': razorpay_order['id'],
#         'razorpay_key_id': settings.RAZORPAY_KEY_ID,
#         'amount': order_amount,
#         'currency': order_currency,
#         'plan_name': plan.name
#     }, status=200)
    


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def handle_payment_callback(request):
    payload = request.data
    razorpay_order_id = payload.get('razorpay_order_id')
    razorpay_payment_id = payload.get('razorpay_payment_id')
    razorpay_signature = payload.get('razorpay_signature')

    # Initialize Razorpay client
    razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))

    try:
        # Verify payment signature
        razorpay_client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        })

        # Retrieve the UserProfile based on the razorpay_order_id
        try:
            user_profile = UserProfile.objects.get(razorpay_order_id=razorpay_order_id)
        except UserProfile.DoesNotExist:
            return Response({'message': 'Order not found for this user profile.'}, status=404)

        # Get current plan and update user profile
        plan = user_profile.current_plan  # Ensure `current_plan` is set on user_profile
        user_profile.plan_name = plan.name
        user_profile.plan_expiry_date = timezone.now() + timedelta(days=plan.duration_days)
        user_profile.plan_status = 'active'
        user_profile.razorpay_payment_id = razorpay_payment_id
        user_profile.save()

        return Response({'message': 'Payment successful, plan activated!'}, status=200)

    except razorpay.errors.SignatureVerificationError:
        return Response({'message': 'Invalid payment signature.'}, status=400)

    except Exception as e:
        # Log error for debugging
        print(f"Error processing payment callback: {e}")
        return Response({'message': 'An error occurred during payment processing.'}, status=500)



    # from rest_framework.decorators import api_view, permission_classes
    # from rest_framework.permissions import IsAuthenticated
    # from rest_framework.response import Response
    # from rest_framework import status
    # import razorpay
    # import logging
    # from .models import Order

    # # Configure logger
    # logger = logging.getLogger(__name__)

    # # Assuming you have initialized Razorpay client elsewhere in your code
    # razorpay_client = razorpay.Client(auth=("RAZORPAY_KEY_ID", "RAZORPAY_SECRET_KEY"))

# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def get_order_details(request):
#     try:
#         # Fetch the user profile
#         user_profile = request.user.userprofile
#         order = Order.objects.filter(user=request.user, razorpay_order_id=user_profile.razorpay_order_id).first()
#         # Check if order ID exists
#         if not user_profile.razorpay_order_id:
#             return Response({'message': 'No order found.'}, status=status.HTTP_404_NOT_FOUND)
        
#         # Fetch Razorpay order ID
#         razorpay_order_id = user_profile.razorpay_order_id

#         # Fetch the order details from Razorpay using the Razorpay Client
#         razorpay_order = razorpay_client.order.fetch(razorpay_order_id)
        
#         # Fetch payment details if available
#         payment_details = razorpay_client.payment.fetch_all({'order_id': razorpay_order_id})['items']
        
#         # Organize payment and transaction details
#         payment_data = [
#             {
#                 'payment_id': payment['id'],
#                 'amount': payment['amount'] / 100,  # Convert from paise to INR
#                 'currency': payment['currency'],
#                 'status': payment['status'],
#                 # 'method': payment['method'],
#                 'captured_at': payment['captured_at'] if 'captured_at' in payment else None,
#             }

#             for payment in payment_details
#         ]

#         data = {
#             'username': request.user.username,  # Username
#             'plan_name': user_profile.plan_name,  # Plan name
#             'razorpay_order_id': razorpay_order['id'],
#             'transaction_id': order.razorpay_payment_id,
#             'amount': razorpay_order['amount'] / 100,  # Convert from paise to INR
#             'currency': razorpay_order['currency'],
#             'status': razorpay_order['status'],
#             'created_at': razorpay_order['created_at'],
#             'payment_details': payment_data  # Transaction and payment details
#         }
        
#         return Response(data, status=status.HTTP_200_OK)
    
#     except UserProfile.DoesNotExist:
#         return Response({'message': 'User profile not found.'}, status=status.HTTP_404_NOT_FOUND)
#     except razorpay.errors.RazorpayError as e:
#         logger.error(f"Error fetching Razorpay order details: {e}")
#         return Response({'message': 'Error fetching Razorpay order details.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from rest_framework import status
# from .models import Order

# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def save_transaction(request):
#     try:
#         # Fetch the transaction ID and Razorpay order ID from the frontend request
#         transaction_id = request.data.get('transaction_id')
#         razorpay_order_id = request.data.get('razorpay_order_id')

#         # Validate the input data
#         if not transaction_id or not razorpay_order_id:
#             return Response({'message': 'Transaction ID and Order ID are required.'}, status=status.HTTP_400_BAD_REQUEST)

#         # Find the order using the Razorpay order ID
#         order = Order.objects.filter(razorpay_order_id=razorpay_order_id).first()

#         if not order:
#             return Response({'message': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

#         # Save the transaction ID in the order record
#         order.transaction_id = transaction_id
#         order.payment_status = 'Completed'  # or update accordingly if needed
#         order.save()

#         return Response({'message': 'Transaction ID saved successfully.'}, status=status.HTTP_200_OK)

#     except Exception as e:
#         return Response({'message': f'Error saving transaction ID: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# from rest_framework.permissions import AllowAny

# # @api_view(['POST'])
# # @permission_classes([IsAuthenticated])
# # def handle_payment_callback(request):
# #     payload = request.data
# #     razorpay_order_id = payload.get('razorpay_order_id')
# #     razorpay_payment_id = payload.get('razorpay_payment_id')
# #     razorpay_signature = payload.get('razorpay_signature')

# #     # Initialize Razorpay client
# #     razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))

# #     try:
# #         # Retrieve the UserProfile based on the razorpay_order_id
# #         check=razorpay_client.utility.verify_payment_signature({
# #             'razorpay_order_id': razorpay_order_id,
# #             'razorpay_payment_id': razorpay_payment_id,
# #             'razorpay_signature': razorpay_signature
# #         })
        
# #         if check is not None:
# #             return Response({'message': 'Invalid payment signature.'}, status=400)
        
# #         user_profile = UserProfile.objects.get(razorpay_order_id=razorpay_order_id)
# #         if user_profile is not None:
# #             return Response({'message': 'Order not found for this user profile.'}, status=404)
# #         plan = user_profile.current_plan  # Ensure `current_plan` is set on user_profile

# #         # Verify payment signature
# #         # Update user's profile with plan details upon successful verification
# #         user_profile.plan_name = plan.name
# #         user_profile.plan_expiry_date = timezone.now() + timedelta(days=plan.duration_days)
# #         user_profile.plan_status = 'active'
# #         user_profile.save()

# #         return Response({'message': 'Payment successful, plan activated!'}, status=200)

# #     # except UserProfile.DoesNotExist:
# #     except Exception as e:
# #         # Log error for debugging and return general failure response
# #         print(f"Error processing payment callback: {e}")
# #         return Response({'message': 'An error occurred during payment processing.'}, status=500)


