"""Capture a real CLI session via a pseudo-terminal into timestamped segments.

Uses standard library only. The JSON transcript is for producing the separate
system demonstration, not a substitute for the group's face-visible presentation.
"""
import errno
import json
import os
from pathlib import Path
import pty
import select
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]


def read_until(master, marker, timeout=5):
    data = bytearray()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if select.select([master], [], [], 0.1)[0]:
            try:
                chunk = os.read(master, 65536)
            except OSError as exc:
                if exc.errno == errno.EIO:
                    break
                raise
            if not chunk:
                break
            data.extend(chunk)
            if marker and marker.encode() in data:
                break
    else:
        raise RuntimeError(f'CLI did not return expected prompt: {marker}')
    return data.decode('utf-8').replace('\r\n', '\n')


def capture():
    commands = [
        ('Four record types', 'add text "Buy milk and coffee"', 'pim> '),
        ('Tasks have descriptions and deadlines', 'add task "Submit report" --deadline 2026-11-19 20:00', 'pim> '),
        ('Events retain start and alarm timestamps', 'add event "Team meeting" --start 2026-10-12 09:00 --alarm 2026-10-12 08:30', 'pim> '),
        ('Contacts preserve text and leading zeroes', 'add contact --name Alice --address "Hong Kong" --mobile "+852 01234567"', 'pim> '),
        ('All records show their ID, type and fields', 'print all', 'pim> '),
        ('Compound search: type, date and negation', 'search type = task && deadline < 2027-01-01 && !description contains "cancelled"', 'pim> '),
        ('Quoted multiword search', 'search text contains "milk and coffee"', 'pim> '),
        ('Edit the selected record', 'edit 2 --deadline 2026-11-20 12:00', 'pim> '),
        ('The deadline is updated', 'print 2', 'pim> '),
        ('Invalid IDs produce a friendly error', 'print abc', 'pim> '),
        ('Unknown fields cannot silently change data', 'edit 2 --unknown typo', 'pim> '),
        ('Save a validated snapshot', 'save demo.pim', 'pim> '),
        ('Delete only the selected record', 'delete 1', 'pim> '),
        ('Confirm before replacing unsaved changes', 'load demo.pim', '[y/N] '),
        ('Load the previous snapshot', 'y', 'pim> '),
        ('The deleted note has been restored', 'print all', 'pim> '),
        ('Clean exit after loading', 'exit', None),
    ]
    with tempfile.TemporaryDirectory() as folder:
        master, slave = pty.openpty()
        process = subprocess.Popen([sys.executable, '-u', str(ROOT / 'main.py')], stdin=slave, stdout=slave, stderr=slave, cwd=folder)
        os.close(slave)
        try:
            segments = [{'caption': 'Real application execution: COMP3211 PIM', 'output': read_until(master, 'pim> '), 'seconds': 5}]
            for caption, command, marker in commands:
                os.write(master, (command + '\n').encode())
                output = read_until(master, marker)
                segments.append({'caption': caption, 'command': command, 'output': output, 'seconds': 7})
            process.wait(timeout=5)
            if process.returncode:
                raise RuntimeError(f'CLI failed: {process.returncode}')
        finally:
            os.close(master)
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
    return {'provenance': 'stdout/stderr captured from the real main.py process via PTY; captions/pacing added for readability',
            'python': sys.version.split()[0], 'segments': segments}


if __name__ == '__main__':
    output = ROOT / 'output' / 'demo'
    output.mkdir(parents=True, exist_ok=True)
    path = output / 'session.json'
    path.write_text(json.dumps(capture(), ensure_ascii=False, indent=2), encoding='utf-8')
    print(path)
