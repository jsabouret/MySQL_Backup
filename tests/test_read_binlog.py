#!/usr/bin/python3
# -*- coding: utf-8 -*-

import struct

bin_log_file = "/backups/mysql2/log/log_2022-07-18/mysql-bin.000030"
file_pointer = 0
with open(bin_log_file, 'rb') as f:
    magic = f.read(4)
    # 0xfe, 0x62, 0x69, 0x6e
    assert magic == b"\xfe\x62\x69\x6e"

    # or

    assert magic == b"\xfebin"

    # update the file pointer to 4
    file_pointer += len(magic)

    # At 4
    # read the header
    # https://dev.mysql.com/doc/internals/en/event-classes-and-types.html
    header_length = 19
    header = f.read(header_length)
    file_pointer += header_length
    unpacked = struct.unpack('<IBIIIH', header)
    timestamp = unpacked[0]
    event_type = unpacked[1]
    server_id = unpacked[2]
    event_size = unpacked[3]
    log_pos = unpacked[4]
    print(f"timestamp:{timestamp}\n"
          f"event_type:{event_type}\n"
          f"server_id: {server_id}\n"
          f"event_size: {event_size}\n"
          f"next_log_pos: {log_pos}")

    # body = f.read(event_size - header_length)
    print("body size", event_size - header_length)
    version = f.read(2)
    file_pointer += 2
    print("binlog version", struct.unpack('<H', version)[0])
    server_version = f.read(50)
    file_pointer += 50
    # s is chart[] in bytes
    print("server version", struct.unpack('<50s', server_version)[0].decode())
    timestamp = f.read(4)
    file_pointer += 4
    # is empty and follow the timestamp of header
    print("timestamp", struct.unpack('<i', timestamp)[0])

    # the remaining has no use as for v4
    # 2 + 50 + 4 = 56
    _ = f.read(event_size - 19 - 56)
    file_pointer += (event_size - 19 - 56)


