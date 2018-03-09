from flask import Flask, request, jsonify
import datetime
import requests
import dateutil.parser as dp

app = Flask(__name__)

INFLUX_URL = 'http://localhost:8086/write?precision=ms&db=location'
LOGFILE = '/tmp/location.log'


@app.route('/overland/ping', methods=['GET'])
def ping():
    return jsonify('pong')


@app.route('/overland/alert', methods=['POST'])
def alert():
    with open(LOGFILE, 'a+') as f:
        f.write('{} -- alerted with {}\n'.format(str(datetime.datetime.now()), request.json))
    return jsonify('pong')


@app.route('/overland', methods=['POST'])
def overland():
    if request.json:
        influx_data = []
        locations = request.json['locations']
        for location in locations:
            if location['type'] == 'Feature':
                lat, _long = location['geometry']['coordinates']

                props = location['properties']
                timestamp = int(dp.parse(props['timestamp']).strftime('%s')) * 1000 # ms

                influx_data.append('location,devid={devid} lat={lat},long={_long},alt={alt},alt_accuracy={v_acc},pos_accuracy={h_acc} {timestamp}'.format(
                    devid=props['device_id'],
                    lat=lat,
                    _long=_long,
                    alt=props['altitude'],
                    v_acc=props['vertical_accuracy'],
                    h_acc=props['horizontal_accuracy'],
                    timestamp=timestamp))

                # motion = driving, walking, running, cycling, stationary
                influx_data.append('motion,devid={devid} driving={driving},walking={walking},running={running},cycling={cycling},stationary={stationary},speed={speed} {timestamp}'.format(
                     devid=props['device_id'],
                     driving='driving' in props['motion'],
                     walking='walking' in props['motion'],
                     running='running' in props['motion'],
                     cycling='cycling' in props['motion'],
                     stationary='stationary' in props['motion'],
                     speed=props['speed'],
                     timestamp=timestamp))
 
                influx_data.append('ios_battery,devid={devid} level={level},state="{state}" {timestamp}'.format(
                    devid=props['device_id'],
                    level=props['battery_level'],
                    state=props['battery_state'],
                    timestamp=timestamp))

        try:
            blob = '\n'.join(influx_data)
            r = requests.post(INFLUX_URL, data=blob)
            r.raise_for_status()
        except:
            print r.content
            raise
    return jsonify({'result': 'ok'})


if __name__ == '__main__':
    app.run(debug=False)
