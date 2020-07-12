#!/usr/bin/env python3
import os, signal, sys
from typing import Callable, Dict
from datetime import datetime, timezone
from urllib.parse import parse_qs

from airos_tools import AirOS
from prometheus_client import Counter, Gauge, generate_latest, CollectorRegistry
import bjoern

# mime="application/openmetrics-text"
mime="text/plain"

def common_log(environ: Dict, status, size):
    print(f'PID {os.getpid()}::', environ.get('REMOTE_ADDR', 'Unknown'), '-', '-',
        datetime.now().astimezone(timezone.utc).strftime('%d/%b/%Y:%H:%M:%S %z'),
        f"\"{environ['REQUEST_METHOD']} "
        f"{environ.get('PATH_INFO', '') + ('?{}'.format(environ['QUERY_STRING']) if environ.get('QUERY_STRING') else '')} "
        f"{environ['SERVER_PROTOCOL']}\"",
        status, 
        size
    )

def application(environ: Dict, start_response: Callable):
    path = environ['PATH_INFO']
    q = parse_qs(environ.get('QUERY_STRING'))
    target=q.get('target', [None])[0]
    if path != '/metrics' and path != '/metrics/':
        status = "404 Not Found"
        body = b''
        size = str(len(body))
        common_log(environ, '404', size)
    elif not target:
        status = "500 Internal Server Error"
        body = b'No target parameter'
        size = str(len(body))
        common_log(environ, '500', size)
    else:
        r = CollectorRegistry()
        try:
            with AirOS(hostname=target, password=UBNT_PASSWORD) as airos:

                labels = {  
                    "device_id": airos.mcastatus.get('deviceId'),
                    "device_name": airos.mcastatus.get('deviceName'),
                    "ap_mac": airos.mcastatus.get('apMac'),
                    "wireless_mode": airos.mcastatus.get('wlanOpmode', '')
                }

                Gauge("airos_wlan_tx_rate_mbps", 'Radio TX rate', labels.keys(), registry=r).labels(**labels).set(
                    airos.mcastatus.get("wlanTxRate"))

                Gauge("airos_wlan_rx_rate_mbps", 'Radio RX rate', labels.keys(), registry=r).labels(**labels).set(
                    airos.mcastatus.get("wlanRxRate"))

                Gauge("airos_signal_dbm", 'Signal', labels.keys(), registry=r).labels(**labels).set(
                    airos.mcastatus.get("signal"))

                Gauge("airos_chanbw_mhz", 'Channel Width', labels.keys(), registry=r).labels(**labels).set(
                    airos.mcastatus.get("chanbw"))

                Gauge("airos_center_freq_mhz", 'Frequency', labels.keys(), registry=r).labels(**labels).set(
                    airos.mcastatus.get("centerFreq"))

                Gauge("airos_tx_power_dbm", 'TX Power', labels.keys(), registry=r).labels(**labels).set(
                    airos.mcastatus.get("txPower"))

                Gauge("airos_antenna_gain_dbm", 'Antenna Gain, dBi', labels.keys(), registry=r).labels(**labels).set(
                    airos.status.get("board", {}).get("radio", [{}])[0].get("antenna", [{}])[0].get("gain", 0))

                Gauge("airos_chain_0_signal_dbm", 'Chan 0 Signal', labels.keys(), registry=r).labels(**labels).set(
                    airos.mcastatus.get("chain0Signal"))

                Gauge("airos_chain_1_signal_dbm", 'Chan 1 Signal', labels.keys(), registry=r).labels(**labels).set(
                    airos.mcastatus.get("chain1Signal"))

                Gauge("airos_noise_dbm", 'Noise Floor', labels.keys(), registry=r).labels(**labels).set(
                    airos.mcastatus.get("noise"))

                Gauge("airos_lan_plugged", 'LAN plugged', labels.keys(), registry=r).labels(**labels).set(
                    airos.mcastatus.get("lanPlugged"))

                Gauge("airos_ccq_percent", 'CCQ', labels.keys(), registry=r).labels(**labels).set(
                    float(airos.mcastatus.get("ccq")) / 10)

                Gauge("airos_remote_devices", 'Remote Devices', labels.keys(), registry=r).labels(**labels).set(
                    len(airos.wstalist))

                Gauge("airos_remote_devices_extra_reporting", 'Remote Devices with Extra Reporting', labels.keys(), registry=r).labels(**labels).set(
                    len([1 for s in airos.wstalist if "remote" in s]))

                Counter("airos_lan_rx_packets_total", "LAN RX packets", labels.keys(), registry=r).labels(**labels).inc(
                    int(airos.mcastatus.get("lanRxPackets")))

                Counter("airos_lan_tx_packets_total", "LAN TX packets", labels.keys(), registry=r).labels(**labels).inc(
                    int(airos.mcastatus.get("lanTxPackets")))

                Counter("airos_wlan_rx_packets_total", "WLAN RX packets", labels.keys(), registry=r).labels(**labels).inc(
                    int(airos.mcastatus.get("wlanRxPackets")))

                Counter("airos_wlan_tx_packets_total", "WLAN TX packets", labels.keys(), registry=r).labels(**labels).inc(
                    int(airos.mcastatus.get("wlanTxPackets")))

                Counter("airos_lan_rx_bytes_total", "LAN RX bytes", labels.keys(), registry=r).labels(**labels).inc(
                    int(airos.mcastatus.get("lanRxBytes")))

                Counter("airos_lan_tx_bytes_total", "LAN TX bytes", labels.keys(), registry=r).labels(**labels).inc(
                    int(airos.mcastatus.get("lanTxBytes")))

                Counter("airos_wlan_rx_bytes_total", "WLAN RX bytes", labels.keys(), registry=r).labels(**labels).inc(
                    int(airos.mcastatus.get("wlanRxBytes")))

                Counter("airos_wlan_tx_bytes_total", "WLAN TX bytes", labels.keys(), registry=r).labels(**labels).inc(
                    int(airos.mcastatus.get("wlanTxBytes")))

                Gauge('airos_error', '', labels.keys(), registry=r).labels(**labels).set(0)

        except Exception as e:
            Gauge('airos_error', '', ['error'], registry=r).labels(error=str(e)).set(1)
            
        status = "200 OK"
        body = generate_latest(registry=r)
        size = str(len(body))
        common_log(environ, '200', size)

    headers = [
        ('Content-Type', mime),
        ('Content-Length', size)
    ]
    start_response(status, headers)
    return body

if __name__ == "__main__":
    WORKERS = int(os.environ.get('WORKERS', '8'))
    PORT = int(os.environ.get('PORT', '8890'))
    UBNT_PASSWORD = os.environ.get('UBNT_PASSWORD', 'ubnt')

    print(f'Staring at http://0.0.0.0:{PORT}/metrics (use PORT environment variable to change).', file=sys.stderr)
    bjoern.listen(application, '0.0.0.0', PORT)

    worker_pids = []
    print('Workers', end='', file=sys.stderr)
    for _ in range(WORKERS):
        pid = os.fork()
        if pid > 0: # in master
            worker_pids.append(pid)
            print('', pid, end='', file=sys.stderr)
        elif pid == 0: # in worker
            try:
                bjoern.run()
            except:
                pass
            exit()
    print(' started (use WORKERS environment variable to change number of workers).', file=sys.stderr)

    # all for one
    try:
        pid, _ = os.wait() 
        print('Child process', pid, 'terminates.', file=sys.stderr)
    except:
        pass
    print('Terminating child processes:', end='', file=sys.stderr)
    for pid in worker_pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except:
            pass
        else:
            print('', pid, end='', file=sys.stderr)
    print('. Exiting.', file=sys.stderr)