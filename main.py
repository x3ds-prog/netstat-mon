#!/usr/bin/env python3

import re
import json
import subprocess

def parse_udp_section(section_lines):
    udp_data = {}
    for line in section_lines:
        # Если строка начинается с числа, то это ключ
        if re.match(r'^\d', line.strip()):
            key_value = re.split(r'\s+', line.strip(), maxsplit=1)
            key = key_value[1].lower().replace(' ', '_').replace(':', '')
            value = key_value[0]
            udp_data[key] = value
        # Если строка начинается с буквы, то это исключительное значение
        elif re.match(r'^[a-zA-Z]', line.strip()):
            key, value = line.strip().split(':', maxsplit=1)
            udp_data[key.strip()] = value.strip()
    return udp_data

def parse_other_section(section_lines):
    other_data = {}
    for line in section_lines:
        # Используем регулярное выражение для извлечения ключа и значения
        match = re.match(r'^\s*(.+?):\s*(\d+)(?:\s+.*)?$', line)
        if match:
            key = match.group(1).lower().replace(' ', '_').replace(':', '')
            value = match.group(2)
            other_data[key] = value
        else:
            # Если строка не соответствует ожидаемому формату, игнорируем ее
            continue
    return other_data

def get_tcp_netstat_output():
    # Выполняем команду netstat -antus и возвращаем ее вывод
    process = subprocess.Popen(["netstat", "-antus"], stdout=subprocess.PIPE)
    output, _ = process.communicate()
    return output.decode("utf-8")

def get_interface_stats():
    # Выполняем команду netstat -i и возвращаем ее вывод
    process = subprocess.Popen(["netstat", "-i"], stdout=subprocess.PIPE)
    output, _ = process.communicate()
    data = output.decode("utf-8")
    lines = data.split('\n')
    lines = lines[1:-1]
    return lines

def get_netstat_output():
    # Выполняем команду netstat -anus и возвращаем ее вывод
    process = subprocess.Popen(["netstat", "-anus"], stdout=subprocess.PIPE)
    output, _ = process.communicate()
    return output.decode("utf-8")

def parse_iface_section(section_lines):
    iface_data = {}
    # Перебираем строки секции
    for line in section_lines:
        # Используем регулярное выражение для извлечения значений
        match = re.match(r'^(\S+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\w+)', line.strip())
        if match:
            # Извлекаем значения
            iface = match.group(1)
            mtu = match.group(2)
            rx_ok = match.group(3)
            rx_err = match.group(4)
            rx_drp = match.group(5)
            rx_ovr = match.group(6)
            tx_ok = match.group(7)
            tx_err = match.group(8)
            tx_drp = match.group(9)
            tx_ovr = match.group(10)
            # Записываем значения в словарь
            iface_data[iface] = {
                'name': iface,
                'MTU': mtu,
                'RX-OK': rx_ok,
                'RX-ERR': rx_err,
                'RX-DRP': rx_drp,
                'RX-OVR': rx_ovr,
                'TX-OK': tx_ok,
                'TX-ERR': tx_err,
                'TX-DRP': tx_drp,
                'TX-OVR': tx_ovr
            }
    return iface_data


def parse_netstat_output(output):
    parsed_data = {}
    current_section = None
    section_lines = []

    for line in output.split('\n'):
        if not line.strip():
            continue

        # Если находим новую секцию, сохраняем предыдущую
        if line.strip().endswith(':'):
            if current_section:
                # Парсим данные текущей секции в зависимости от ее типа
                if current_section.lower() == "udp":
                    parsed_data[current_section] = parse_udp_section(section_lines)
                elif current_section.lower() == "tcp":
                    parsed_data[current_section] = parse_udp_section(section_lines)
                else:
                    parsed_data[current_section] = parse_other_section(section_lines)
            current_section = line.strip().strip(':')
            section_lines = []
        else:
            section_lines.append(line.strip())

    # Парсим последнюю секцию
    if current_section:
        if current_section.lower() == "udp":
            parsed_data[current_section] = parse_udp_section(section_lines)
        elif current_section.lower() == "tcp":
            parsed_data[current_section] = parse_udp_section(section_lines)
        else:
            parsed_data[current_section] = parse_other_section(section_lines)

    interface_stats = parse_iface_section(get_interface_stats())
    parsed_data['interfaces'] = interface_stats

    return parsed_data


def main():
    #netstat_output = get_netstat_output()
    netstat_output = get_tcp_netstat_output()
    parsed_data = parse_netstat_output(netstat_output)

    # Преобразуем в JSON и выводим
    json_data = json.dumps(parsed_data, indent=4, separators=(',', ': '), ensure_ascii=False)
    print(json_data)

if __name__ == "__main__":
    main()
