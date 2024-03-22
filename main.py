from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from collections import defaultdict, deque
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
socketio = SocketIO(app)

# Dictionary to store message queue for each user
message_queues = defaultdict(deque)
# Dictionary to store timestamp of last message for each user
last_message_timestamps = defaultdict(int)
# Dictionary to store message count for each user
message_count = defaultdict(int)
# Dictionary to store cooldown timer for each user
cooldown_timers = defaultdict(int)


@app.route('/', methods=['GET', 'POST'])
def sessions():
    return render_template('session.html')


def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')


@socketio.on('my event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    message = json['message']
    username = json['user_name']

    # Check if message and username lengths are valid
    if len(message) >= 1 and 4 < len(username) <= 15:
        print('received my event: ' + str(json))

        # Check if the same message has been sent more than 5 times within 10 seconds
        if message_count[username] >= 5 and message_queues[username] and message_queues[username][-1] == message:
            if time.time() - last_message_timestamps[username] <= 10:
                # Check if cooldown timer is active
                if cooldown_timers[username] == 0:
                    # Start cooldown timer
                    cooldown_timers[username] = time.time() + 5
                    error_message = 'You are sending the same message too frequently. Please wait.'
                    print('Cooldown activated:', error_message)
                    emit('validation error', {'error': error_message}, room=request.sid)  # Emit the error message to the sender only
                    return
                elif time.time() < cooldown_timers[username]:
                    # Still in cooldown, emit cooldown message
                    error_message = 'You are sending the same message too frequently. Please wait.'
                    print('In cooldown:', error_message)
                    emit('validation error', {'error': error_message}, room=request.sid)  # Emit the error message to the sender only
                    return

        # If the queue length exceeds 5, remove the oldest message
        if len(message_queues[username]) > 5:
            message_queues[username].popleft()

        # Update message count and timestamp
        message_count[username] += 1
        last_message_timestamps[username] = time.time()

        # Append message to the queue
        message_queues[username].append(message)

        # Reset cooldown timer
        cooldown_timers[username] = 0

        # Emit the message to all clients including the sender
        emit('my response', {'user_name': username, 'message': message}, broadcast=True)

    else:
        error_message = ''
        if len(message) < 1:
            error_message += 'Message must be at least 1 character long. '
        if len(username) <= 4:
            error_message += 'Username must be longer than 4 characters. '
        if len(username) > 15:
            error_message += 'Username must be 15 characters or shorter. '
        print('Validation error:', error_message)
        emit('validation error', {'error': error_message}, room=request.sid)  # Emit the error message to the sender only


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True, debug=True)
