import pandas as pd

def extract_server_info(data):
    server_info = []
    lines = data.split('\n')
    for line in lines:
        options = line.split()
        if len(options) >= 3 and options[0] == 'add' and options[1] == 'server':
            server_name = options[2]
            server_ip = options[3]
            server_info.append(['create', 'ltm', 'node', server_ip, server_name])

    df = pd.DataFrame(server_info, columns=['Command', 'Type', 'Node', 'IP Address', 'Server Name'])
    return df

def extract_lb_monitor_info(data):
    lb_monitor_info = []
    lines = data.split('\n')
    for line in lines:
        options = line.split()
        if len(options) >= 5 and options[0] == 'add' and options[1] == 'lb' and options[2] == 'monitor':
            monitor_name = options[3]
            monitor_type = options[4]
            remaining_options = options[5:]
            monitor_options = {}
            dest_port = None
            for i, option in enumerate(remaining_options):
                if option.startswith('-'):
                    field_name = option[1:]
                    if i + 1 < len(remaining_options) and not remaining_options[i + 1].startswith('-'):
                        value = remaining_options[i + 1]
                        if field_name == 'destPort':
                            dest_port = value
                        if field_name == 'httpRequest':
                            http_request = value
                    else:
                        value = 'True'  # Assuming True for options without a value
                    monitor_options[field_name] = value

            if monitor_type == "TCP":
                formatted_monitor = ['ltm monitor create', 'tcp', monitor_name, 'destination *:', f"{dest_port}"]
                lb_monitor_info.append(formatted_monitor)
            if monitor_type == "HTTP":
                formatted_monitor = ['ltm monitor create', 'http', monitor_name, 'destination *:', f"{dest_port}", 'send', f"{http_request}" ]
                lb_monitor_info.append(formatted_monitor)

            else:
                lb_monitor_info.append([monitor_name, monitor_type] + list(monitor_options.values()))

    df = pd.DataFrame(lb_monitor_info)
    return df

def extract_data_from_file(filename):
    with open(filename, 'r') as f:
        data = f.read()
    return data

def process_data(data):
    server_df = extract_server_info(data)
    lb_monitor_df = extract_lb_monitor_info(data)

    return server_df, lb_monitor_df

# Read data from nsprod.conf
data = extract_data_from_file('nsprod.conf')
# Process data
server_df, lb_monitor_df = process_data(data)

# Write to Excel
with pd.ExcelWriter('f5_config.xlsx') as writer:
    server_df.to_excel(writer, sheet_name='Servers', index=False)
    lb_monitor_df.to_excel(writer, sheet_name='Monitors', index=False)

