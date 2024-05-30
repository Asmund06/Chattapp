from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from collections import defaultdict, deque
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
socketio = SocketIO(app)

# Ordbok for å lagre meldingskø for hver bruker
message_queues = defaultdict(deque)
# Ordbok for å lagre tidspunktet for siste melding for hver bruker
last_message_timestamps = defaultdict(int)
# Ordbok for å lagre antall meldinger for hver bruker
message_count = defaultdict(int)
# Ordbok for å lagre nedkjølingstimer for hver bruker
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

    # Sjekk om meldingslengde og brukernavn er gyldige
    if len(message) >= 1 and 4 < len(username) <= 15:
        print('received my event: ' + str(json))

        # Sjekk om den samme meldingen er sendt mer enn 5 ganger innenfor 10 sekunder
        if message_count[username] >= 5 and message_queues[username] and message_queues[username][-1] == message:
            if time.time() - last_message_timestamps[username] <= 10:
                # Sjekk om nedkjølingstimer er aktive
                if cooldown_timers[username] == 0:
                    # Start nedkjølingstimer
                    cooldown_timers[username] = time.time() + 5
                    error_message = 'You are sending the same message too frequently. Please wait.'
                    print('Cooldown activated:', error_message)
                    emit('validation error', {'error': error_message}, room=request.sid)  # Send feilmeldingen kun til avsenderen
                    return
                elif time.time() < cooldown_timers[username]:
                    # Fortsatt i nedkjøling, send nedkjølingsmelding
                    error_message = 'You are sending the same message too frequently. Please wait.'
                    print('In cooldown:', error_message)
                    emit('validation error', {'error': error_message}, room=request.sid)  # Emit the error message to the sender only
                    return

        # Hvis kølengden overstiger 5, fjern den eldste meldingen
        if len(message_queues[username]) > 5:
            message_queues[username].popleft()

        # Oppdater meldingsantall og tidspunkt
        message_count[username] += 1
        last_message_timestamps[username] = time.time()

        # Legg til meldingen i køen
        message_queues[username].append(message)

        # Tilbakestill nedkjølingstimer
        cooldown_timers[username] = 0

        # Send meldingen til alle klienter, inkludert avsenderen
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
        emit('validation error', {'error': error_message}, room=request.sid)  # Send feilmeldingen kun til avsenderen


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True, debug=True)