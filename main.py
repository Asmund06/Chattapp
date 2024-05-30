from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from collections import defaultdict, deque
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
socketio = SocketIO(app)

# Ordbok for å lagre meldingskø for hver bruker
meldingskøer = defaultdict(deque)
# Ordbok for å lagre tidspunktet for siste melding for hver bruker
siste_melding_tidspunkt = defaultdict(int)
# Ordbok for å lagre antall meldinger for hver bruker
antall_meldinger = defaultdict(int)
# Ordbok for å lagre nedkjølingstimer for hver bruker
nedkjølingstimer = defaultdict(int)

@app.route('/', methods=['GET', 'POST'])
def økter():
    return render_template('session.html')

# Funksjon for å håndtere mottatte meldinger
def melding_mottatt(metoder=['GET', 'POST']):
    print('melding ble mottatt!!!')

# Hendelseshåndterer for 'min hendelse'
@socketio.on('min hendelse')
def håndter_min_egendefinerte_hendelse(json, metoder=['GET', 'POST']):
    # Hent melding og brukernavn fra JSON-data
    melding = json['melding']
    brukernavn = json['brukernavn']

    # Sjekk om meldings- og brukernavnslengdene er gyldige
    if len(melding) >= 1 and 4 < len(brukernavn) <= 15:
        print('mottok min hendelse: ' + str(json))

        # Sjekk om den samme meldingen er sendt mer enn 5 ganger innenfor 10 sekunder
        if antall_meldinger[brukernavn] >= 5 and meldingskøer[brukernavn] and meldingskøer[brukernavn][-1] == melding:
            if time.time() - siste_melding_tidspunkt[brukernavn] <= 10:
                # Sjekk om nedkjølingstimeren er aktiv
                if nedkjølingstimer[brukernavn] == 0:
                    # Start nedkjølingstimeren
                    nedkjølingstimer[brukernavn] = time.time() + 5
                    feilmelding = 'Du sender den samme meldingen for ofte. Vennligst vent.'
                    print('Nedkjøling aktivert:', feilmelding)
                    emit('valideringsfeil', {'feil': feilmelding}, room=request.sid)  # Send feilmeldingen kun til avsenderen
                    return
                elif time.time() < nedkjølingstimer[brukernavn]:
                    # Fortsatt i nedkjøling, send nedkjølingsmelding
                    feilmelding = 'Du sender den samme meldingen for ofte. Vennligst vent.'
                    print('I nedkjøling:', feilmelding)
                    emit('valideringsfeil', {'feil': feilmelding}, room=request.sid)  # Send feilmeldingen kun til avsenderen
                    return

        # Hvis kølengden overstiger 5, fjern den eldste meldingen
        if len(meldingskøer[brukernavn]) > 5:
            meldingskøer[brukernavn].popleft()

        # Oppdater antall meldinger og tidspunkt
        antall_meldinger[brukernavn] += 1
        siste_melding_tidspunkt[brukernavn] = time.time()

        # Legg til melding i køen
        meldingskøer[brukernavn].append(melding)

        # Tilbakestill nedkjølingstimer
        nedkjølingstimer[brukernavn] = 0

        # Send meldingen til alle klienter inkludert avsenderen
        emit('min respons', {'brukernavn': brukernavn, 'melding': melding}, broadcast=True)

    else:
        # Validering mislyktes, konstruer feilmelding
        feilmelding = ''
        if len(melding) < 1:
            feilmelding += 'Meldingen må være minst 1 tegn lang. '
        if len(brukernavn) <= 4:
            feilmelding += 'Brukernavnet må være lengre enn 4 tegn. '
        if len(brukernavn) > 15:
            feilmelding += 'Brukernavnet må være 15 tegn eller kortere. '
        print('Valideringsfeil:', feilmelding)
        emit('valideringsfeil', {'feil': feilmelding}, room=request.sid)  # Send feilmeldingen kun til avsenderen

if __name__ == '__main__':
    # Start SocketIO-serveren
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True, debug=True)
