from django.shortcuts import render
from rest_framework import generics, status
from .serializers import RoomSerializer, CreateRoomSerializer, UpdateRoomSerializer, UserProfileSerializer, UserSerializer
from .models import Room, UserProfile
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from utils import get_users_in_room
from django.shortcuts import get_object_or_404

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

import ast
import operator

from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from .models import Room, MathGame, GameScore, User, Game, ContentType
import random, json

class CurrentUser(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_data = {
            'id': request.user.id,
            'username': request.user.username,
        }
        
        return Response(user_data)
    
class RoomView(generics.ListAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer

class GetRoom(APIView):
    serializer_class = RoomSerializer
    lookup_url_kwarg = 'code'

    def get(self, request, format=None):
        code = request.GET.get(self.lookup_url_kwarg)
        if code != None:
            room = Room.objects.filter(code=code)
            if len(room) > 0:
                data = RoomSerializer(room[0]).data
                data['is_host'] = self.request.session.session_key == room[0].host
                return Response(data, status=status.HTTP_200_OK)
            else:
                return Response({'Room Not Found': "Invalid Room Code"}, status=status.HTTP_404_NOT_FOUND)
        return Response({'Bad Request': 'Code Parameter Not Found in Request'}, status=status.HTTP_400_BAD_REQUEST)
    
class JoinRoom(APIView):
    def post(self, request, format=None):
        code = request.data.get('room_code')
        if code != None:
            room_result = Room.objects.filter(code=code)
            if len(room_result) > 0:
                room = room_result[0]
                profile = request.user.userprofile
                profile.current_room = room
                profile.save()

                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f'room_{code}',
                    {
                        'type': 'user_update',
                        'room_code': code,
                        'message': 'A new user has joined the room!'
                    }
                )

                return Response({'message': 'Room Joined!'}, status=status.HTTP_200_OK)
            return Response({'Bad Request': 'Invalid Room Code'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'Bad Request': 'Invalid post data, did not find a code key'}, status=status.HTTP_400_BAD_REQUEST)


class CreateRoomView(APIView):
    serializer_class = CreateRoomSerializer

    def post(self, request, format=None):
        print("create-room HIT!")
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            print(self.request.data)
            host_id = self.request.data['host']['id']
            host_user = User.objects.get(id=host_id)
            queryset = Room.objects.filter(host=host_user)
            if queryset.exists():
                room = queryset[0]
                return Response(RoomSerializer(room).data, status=status.HTTP_200_OK)
            else:
                room = Room(host=host_user)
                room.save()
                user_profile = UserProfile.objects.get(user=host_user)
                user_profile.current_room = room
                user_profile.save()
                return Response(RoomSerializer(room).data, status=status.HTTP_201_CREATED)
        return Response(RoomSerializer(room).data, status=status.HTTP_400_BAD_REQUEST)

class LeaveRoom(APIView):
    permissionClasses = [IsAuthenticated]
    def post(self, request, format=None):
        user = request.user
        code = request.data.get('room_code', None)
        if not code:
            return Response({'Error': 'Room code is required'}, status=status.HTTP_400_BAD_REQUEST)
        user_profile = user.userprofile

        if user_profile.current_room:
            if user_profile.current_room.host == user:
                room = user_profile.current_room
                room.delete()
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f'room_{code}',
                    {
                        'type': 'room_closed',
                        'message': 'The host has left and the room has been closed.'
                    }
                )
            else:
                user_profile.current_room = None
                user_profile.save()
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f'room_{code}',
                    {
                        'type': 'user_update',
                        'room_code': code,
                        'message': 'A user has left the room!'
                    }
                )

        return Response({'Message': 'Success'}, status=status.HTTP_200_OK)
    
class UpdateRoom(APIView):
    serializer_class = UpdateRoomSerializer

    def patch(self, request, format=None):
        if not self.request.session.exists(self.request.session.session_key):
            self.request.session.create()

        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            code = serializer.data.get('code')

            queryset = Room.objects.filter(code=code)

            if not queryset.exists():
                return Response({'msg': 'Room not found.'}, status=status.HTTP_404_NOT_FOUND)
            
            room = queryset[0]
            user_id = self.request.session.session_key

            if room.host != user_id:
                return Response({'msg': 'You are not the host of this room.'}, status=status.HTTP_403_FORBIDDEN)
        
            return Response(RoomSerializer(room).data, status=status.HTTP_200_OK)

        return Response({'Bad Request': 'Invalid Data...'}, status=status.HTTP_400_BAD_REQUEST)
    
class UsersInRoom(APIView):
    def get(self, request, room_code, format=None):
        data = get_users_in_room(room_code)
        return Response(data, status=status.HTTP_200_OK)

class StartGame(APIView): 
    def post(self, request, room_code):
        try:
            room = Room.objects.get(code=room_code)
            if not room:
                return JsonResponse({"error": "Room not found"}, status=404)

            game = MathGame(user=request.user)
            game.save()

            # Link the game to the room
            room.current_game = game
            room.save()

            return JsonResponse({"message": "Game started"}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
class UserInARoom(APIView):
    def post(self, request):
            try:
                data = json.loads(request.body)
                username = data.get('username')

                user = User.objects.get(username=username)
                user_profile = UserProfile.objects.get(user=user)
                in_room = user_profile.current_room is not None

                if in_room:
                    return JsonResponse({
                        'in_room': True,
                        'room_code': user_profile.current_room.code
                    })
                else:
                    return JsonResponse({'in_room': False})
            except User.DoesNotExist:
                return JsonResponse({'error': 'User not found'}, status=404)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
            
class HostDetails(APIView):
    def get(self, request, *args, **kwargs):
        room_code = kwargs.get('room_code')
        try:
            room = Room.objects.get(code=room_code)
            host_id = room.host.id
            return Response({'host_id': host_id}, status=status.HTTP_200_OK)
        except Room.DoesNotExist:
            return Response({'error: Room Not Found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GenerateEquation(APIView):
    def get(self, request):
        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)
            
        return JsonResponse({
            'equation': f'{num1} + {num2}',
            'answer': num1 + num2
        })

class HandleAnswer(APIView):
    def post(self, request):
        user_answer = request.data.get('user_answer')
        original_equation = request.data.get('original_equation')

        correct = self.check_equation_answer(original_equation, user_answer)

        if correct:
            return Response({'result': 'correct'})
        else:
            return Response({'result': 'incorrect'})
    
    def check_equation_answer(self, equation, answer):
        try:
            result = self.safe_eval(equation)

            return result == float(answer)
        except:
            return False
    
    def safe_eval(self, expr):
        bin_ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
        }

        def _eval(node):
            if isinstance(node, ast.Num):
                return node.n
            elif isinstance(node, ast.BinOp):
                left = _eval(node.left)
                right = _eval(node.right)
                return bin_ops[type(node.op)](left, right)
            else:
                raise ValueError
        return _eval(ast.parse(expr, mode='eval').body)
    
# Endpoint to instantiate a math game
class StartMathGame(APIView):
    def post(self, request):
        try:
            room_code = request.data.get('room_code', None)
            room = Room.objects.get(code=room_code)

            if request.user != room.host:
                return JsonResponse({'error': 'Only the room host can start the game'}, status=403)
            
            math_game = MathGame.objects.create(room=room, name="Math Game")

            return JsonResponse({'message': 'Math game started successfully', 'game_id': math_game.id})
        except Room.DoesNotExist:
            return JsonResponse({'error': 'Room not found'}, status=404)

# Endpoint to update a player's score
class UpdatePlayerScore(APIView):
    def post(self, request, game_id):
        user = request.user
        new_score = request.POST.get('score')

        math_game = MathGame.objects.get(id=game_id)

        content_type = ContentType.objects.get_for_model(MathGame)
        game_score, created = GameScore.objects.update_or_create(
            user=user,
            content_type = content_type,
            object_id=math_game.id,
            defaults={'score': new_score}
        )

        return JsonResponse({'message': 'Score updated successfully'})


# Endpoint to retrive all players' scores for a game
                

