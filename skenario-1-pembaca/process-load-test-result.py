import json
import pandas as pd
import sys
from datetime import datetime
import re

def format_number_id(number, decimal_places=2):
    if decimal_places == 0:
        number_str = str(round(number))
    else:
        number_str = f"{number:.{decimal_places}f}"
    
    if '.' in number_str:
        main_part, decimal_part = number_str.split('.')
    else:
        main_part, decimal_part = number_str, ""
    
    result = ""
    for i, digit in enumerate(reversed(main_part)):
        if i > 0 and i % 3 == 0:
            result = '.' + result
        result = digit + result
    
    if decimal_part:
        result = result + ',' + decimal_part
    
    return result

def parse_ndjson_k6_results(json_file):
    print(f"Memproses file NDJSON: {json_file}")
    
    metrics = {}
    count_metrics = {}
    error_metrics = {}
    
    start_time = None
    end_time = None
    
    try:
        with open(json_file, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    data = json.loads(line)
                    
                    if 'metric' in data and 'type' in data and data['type'] == 'Point':
                        metric_name = data['metric']
                        point_data = data['data']
                        
                        if start_time is None or start_time > point_data['time']:
                            start_time = point_data['time']
                        if end_time is None or end_time < point_data['time']:
                            end_time = point_data['time']
                        
                        value = point_data['value']
                        
                        tags = point_data.get('tags', {})
                        group = tags.get('group', '')
                        
                        step_name = None
                        if group and '::Step ' in group:
                            step_match = re.search(r'::Step \d+: (.+)', group)
                            if step_match:
                                step_name = step_match.group(1)
                        
                        key = f"{step_name}_{metric_name}" if step_name else metric_name
                        
                        if metric_name == 'http_req_duration':
                            if key not in metrics:
                                metrics[key] = []
                            metrics[key].append(value)
                        
                        if metric_name == 'http_req_failed':
                            if key not in error_metrics:
                                error_metrics[key] = []
                            error_metrics[key].append(value)
                        
                        if metric_name in ['http_reqs', 'iterations']:
                            if key not in count_metrics:
                                count_metrics[key] = 0
                            count_metrics[key] += value
                except json.JSONDecodeError as e:
                    print(f"Kesalahan memproses baris JSON: {e}")
                    continue
    except Exception as e:
        print(f"Error membaca file: {e}")
        return None, None, None, None, None
    
    if start_time and end_time:
        try:
            from dateutil import parser
            start_dt = parser.parse(start_time)
            end_dt = parser.parse(end_time)
            test_duration_secs = (end_dt - start_dt).total_seconds()
            test_duration_mins = test_duration_secs / 60
        except Exception as e:
            print(f"Error menghitung durasi: {e}")
            test_duration_mins = 20
    else:
        test_duration_mins = 20
    
    print(f"Durasi pengujian: {test_duration_mins:.2f} menit")
    
    return metrics, count_metrics, error_metrics, test_duration_mins, start_time

def prepare_data_table(metrics, count_metrics, error_metrics, test_duration_mins):
    steps = [
        "Melihat Kategori",
        "Melihat Unit", 
        "Mencari Konten",
        "Melihat Detail Konten",
        "Menambah View Konten"
    ]
    
    step_mapping = {
        "Melihat Kategori": ["Get Categories", "categories"],
        "Melihat Unit": ["Get Units", "units"],
        "Mencari Konten": ["Search Media Item", "media_items_search", "media-items"],
        "Melihat Detail Konten": ["Get Media Item Detail", "media_item_detail", "media-items/{id}"],
        "Menambah View Konten": ["Increment View Count", "view_increment", "media-items/{id}/view"]
    }
    
    df = pd.DataFrame(columns=[
        "Label", 
        "Rata-rata (ms)", 
        "Min (ms)", 
        "Max (ms)", 
        "Standar Deviasi (ms)", 
        "Error (%)", 
        "Throughput (/min)"
    ])
    
    has_general_metrics = 'http_req_duration' in metrics
    
    for i, step in enumerate(steps):
        step_duration_values = None
        step_error_rate = 0
        step_request_count = 0
        
        for possible_name in step_mapping[step]:
            for key in metrics.keys():
                if possible_name.lower() in key.lower():
                    step_duration_values = metrics[key]
                    break
            
            for key in error_metrics.keys():
                if possible_name.lower() in key.lower():
                    if error_metrics[key]:
                        step_error_rate = sum(error_metrics[key]) / len(error_metrics[key]) * 100
                    break
            
            for key in count_metrics.keys():
                if possible_name.lower() in key.lower():
                    step_request_count = count_metrics[key]
                    break
            
            if step_duration_values:
                break
        
        if not step_duration_values and has_general_metrics:
            print(f"Menggunakan metrik umum untuk {step}")
            step_duration_values = metrics['http_req_duration']
            
            if 'http_req_failed' in error_metrics and error_metrics['http_req_failed']:
                step_error_rate = sum(error_metrics['http_req_failed']) / len(error_metrics['http_req_failed']) * 100
            
            if 'http_reqs' in count_metrics:
                step_request_count = count_metrics['http_reqs'] / len(steps)
            elif 'iterations' in count_metrics:
                step_request_count = count_metrics['iterations']
        
        if step_duration_values:
            avg = sum(step_duration_values) / len(step_duration_values)
            min_val = min(step_duration_values)
            max_val = max(step_duration_values)
            
            variance = sum((x - avg) ** 2 for x in step_duration_values) / len(step_duration_values)
            std_dev = variance ** 0.5
            
            throughput = step_request_count / test_duration_mins if test_duration_mins > 0 else 0
            
            df.loc[i] = [
                step,
                format_number_id(avg),
                format_number_id(min_val),
                format_number_id(max_val),
                format_number_id(std_dev),
                format_number_id(step_error_rate, 1),
                format_number_id(throughput, 1)
            ]
        else:
            print(f"Tidak menemukan data untuk {step}, menggunakan N/A")
            df.loc[i] = [step, "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"]
    
    return df

def save_results(df, test_time):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    csv_file = f"load_test_results_{timestamp}.csv"
    df.to_csv(csv_file, index=False)
    
    word_file = f"load_test_results_word_{timestamp}.txt"
    with open(word_file, 'w') as f:
        f.write(df.to_string(index=False))

def process_k6_results(json_file):
    metrics, count_metrics, error_metrics, test_duration_mins, test_time = parse_ndjson_k6_results(json_file)
    
    if metrics is None:
        print("Gagal memproses file. Program dihentikan.")
        return
    
    df = prepare_data_table(metrics, count_metrics, error_metrics, test_duration_mins)
    
    print("\nTabel Performa UI Heritage:")
    print("="*100)
    print(df.to_string(index=False))
    print("="*100)
    
    save_results(df, test_time)
    
    print("\nAnda dapat menyalin tabel ini dan menempelkannya ke aplikasi word processor atau spreadsheet.")

if __name__ == "__main__":
    try:
        import pandas as pd
    except ImportError:
        print("Pandas tidak ditemukan. Mencoba menginstal...")
        import subprocess
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas"])
            import pandas as pd
            print("Pandas berhasil diinstal.")
        except:
            print("Gagal menginstal pandas. Silakan install secara manual dengan perintah:")
            print("pip install pandas")
            sys.exit(1)
    
    try:
        import dateutil
    except ImportError:
        print("python-dateutil tidak ditemukan. Mencoba menginstal...")
        import subprocess
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dateutil"])
            print("python-dateutil berhasil diinstal.")
        except:
            print("Gagal menginstal python-dateutil. Silakan install secara manual dengan perintah:")
            print("pip install python-dateutil")
            sys.exit(1)
    
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    else:
        json_file = input("Masukkan path ke file hasil k6 (NDJSON): ")
    
    process_k6_results(json_file)