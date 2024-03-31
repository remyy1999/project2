def start():
    try:
        with confundo.Socket() as sock:
            sock.settimeout(10)
            sock.connect((args.host, int(args.port)))

            with open(args.file, "rb") as f:
                while True:
                    data = f.read(65536)  # Read 64KB at a time (adjust size as needed)
                    if not data:
                        break  # Break loop if no more data to read
                    total_sent = 0
                    while total_sent < len(data):
                        sent = sock.send(data[total_sent:])
                        if sent == 0:
                            raise RuntimeError("Socket connection broken")
                        total_sent += sent
    except RuntimeError as e:
        sys.stderr.write(f"ERROR: {e}\n")
        sys.exit(1)
