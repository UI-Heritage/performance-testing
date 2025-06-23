import json
import pandas as pd
import sys
from datetime import datetime
import re

def format_number_id(number, decimal_places=2):
    if number is None:
        return "N/A"
        
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
                        
                        if metric_name.endswith('_duration') or metric_name == 'http_req_duration':
                            if key not in metrics:
                                metrics[key] = []
                            metrics[key].append(value)
                        
                        if metric_name.endswith('_failed') or metric_name == 'http_req_failed':
                            if key not in error_metrics:
                                error_metrics[key] = []
                            error_metrics[key].append(value)
                        
                        if metric_name in ['http_reqs', 'iterations'] or metric_name.endswith('_requests'):
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

def prepare_data_table_contributor(metrics, count_metrics, error_metrics, test_duration_mins):
    steps = [
        "SSO Login",
        "Small File Upload",
        "Large File Upload",
        "Media Item Creation"
    ]
    
    metric_mapping = {
        "SSO Login": ["login_duration", "login_failed", "login_requests"],
        "Small File Upload": ["small_file_upload_duration", "small_file_upload_failed", "small_file_upload_requests"],
        "Large File Upload": ["large_file_upload_init_duration", "chunk_upload_duration", "complete_upload_duration", 
                             "large_file_upload_init_failed", "chunk_upload_failed", "complete_upload_failed", 
                             "large_file_upload_init_requests", "chunk_upload_requests", "complete_upload_requests"],
        "Media Item Creation": ["media_item_create_duration", "media_item_create_failed", "media_item_create_requests"]
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
        avg = None
        min_val = None
        max_val = None
        std_dev = None
        error_rate = None
        throughput = None
        
        duration_key = None
        error_key = None
        count_key = None
        
        if step == "Large File Upload":
            init_duration_values = []
            chunk_duration_values = []
            complete_duration_values = []
            
            for metric_name, values in metrics.items():
                if "large_file_upload_init_duration" in metric_name:
                    init_duration_values = values
                elif "chunk_upload_duration" in metric_name:
                    chunk_duration_values = values
                elif "complete_upload_duration" in metric_name:
                    complete_duration_values = values
            
            if init_duration_values:
                avg_init = sum(init_duration_values) / len(init_duration_values)
                min_init = min(init_duration_values) if init_duration_values else 0
                max_init = max(init_duration_values) if init_duration_values else 0
                
                avg_chunk = 0
                min_chunk = 0
                max_chunk = 0
                if chunk_duration_values:
                    chunks_per_file = 4
                    files_count = len(init_duration_values)
                    chunks_per_value = len(chunk_duration_values) / (files_count * chunks_per_file)
                    
                    avg_chunk = sum(chunk_duration_values) / (files_count * chunks_per_value)
                    min_chunk = min(chunk_duration_values) * chunks_per_file if chunk_duration_values else 0
                    max_chunk = max(chunk_duration_values) * chunks_per_file if chunk_duration_values else 0
                
                avg_complete = 0
                min_complete = 0
                max_complete = 0
                if complete_duration_values:
                    avg_complete = sum(complete_duration_values) / len(complete_duration_values)
                    min_complete = min(complete_duration_values) if complete_duration_values else 0
                    max_complete = max(complete_duration_values) if complete_duration_values else 0
                
                avg = avg_init + avg_chunk + avg_complete
                min_val = min_init + min_chunk + min_complete
                max_val = max_init + max_chunk + max_complete
                
                if init_duration_values:
                    variance_init = sum((x - avg_init) ** 2 for x in init_duration_values) / len(init_duration_values)
                    std_dev_init = variance_init ** 0.5
                else:
                    std_dev_init = 0
                    
                if chunk_duration_values:
                    variance_chunk = sum((x - (avg_chunk / 4)) ** 2 for x in chunk_duration_values) / len(chunk_duration_values)
                    std_dev_chunk = variance_chunk ** 0.5 * 4
                else:
                    std_dev_chunk = 0
                    
                if complete_duration_values:
                    variance_complete = sum((x - avg_complete) ** 2 for x in complete_duration_values) / len(complete_duration_values)
                    std_dev_complete = variance_complete ** 0.5
                else:
                    std_dev_complete = 0
                
                std_dev = (std_dev_init**2 + std_dev_chunk**2 + std_dev_complete**2) ** 0.5
                
                count_key = "large_file_upload_init_requests"
                
            else:
                duration_key = "large_file_upload_init_duration"
        else:
            if step in metric_mapping:
                for metric_name in metrics.keys():
                    for pattern in metric_mapping[step]:
                        if pattern in metric_name and metric_name.endswith('_duration'):
                            duration_key = metric_name
                            break
                    if duration_key:
                        break
                
                for metric_name in error_metrics.keys():
                    for pattern in metric_mapping[step]:
                        if pattern in metric_name and metric_name.endswith('_failed'):
                            error_key = metric_name
                            break
                    if error_key:
                        break
                
                for metric_name in count_metrics.keys():
                    for pattern in metric_mapping[step]:
                        if pattern in metric_name and metric_name.endswith('_requests'):
                            count_key = metric_name
                            break
                    if count_key:
                        break
        
        if step != "Large File Upload" or not avg:
            if duration_key and duration_key in metrics:
                duration_values = metrics[duration_key]
                if duration_values:
                    avg = sum(duration_values) / len(duration_values)
                    min_val = min(duration_values)
                    max_val = max(duration_values)
                    
                    variance = sum((x - avg) ** 2 for x in duration_values) / len(duration_values)
                    std_dev = variance ** 0.5
        
        if step == "Large File Upload":
            if "large_file_upload_init_requests" in count_metrics:
                total_attempts = count_metrics["large_file_upload_init_requests"]
                
                if "large_file_upload_init_failed" in error_metrics and error_metrics["large_file_upload_init_failed"]:
                    if "http_req_failed" in error_metrics and len(error_metrics["http_req_failed"]) > 0:
                        http_failure_rate = sum(error_metrics["http_req_failed"]) / len(error_metrics["http_req_failed"])
                        
                        failed_attempts = round(total_attempts * http_failure_rate)
                        
                        if "large_file_upload_init_failed" in error_metrics:
                            failed_rate_samples = error_metrics["large_file_upload_init_failed"]
                            if failed_rate_samples and sum(failed_rate_samples) > 0:
                                failed_count = sum(1 for rate in failed_rate_samples if rate > 0.99)
                                if failed_count > 0:
                                    failed_attempts = failed_count
                        
                        if total_attempts > 0:
                            error_rate = (failed_attempts / total_attempts) * 100
        elif step == "Media Item Creation":
            if "media_item_create_requests" in count_metrics and "media_item_create_failed" in error_metrics:
                total_attempts = count_metrics["media_item_create_requests"]
                error_values = error_metrics["media_item_create_failed"]
                
                if error_values and total_attempts > 0:
                    failed_count = sum(1 for rate in error_values if rate > 0.99)
                    
                    if "checks_failed" in count_metrics and "checks_total" in count_metrics:
                        checks_failed = count_metrics["checks_failed"]
                        checks_total = count_metrics["checks_total"]
                        
                        if checks_total > 0:
                            actual_failure_pct = (checks_failed / checks_total) * 100
                            
                            if actual_failure_pct < 5 and failed_count == len(error_values):
                                error_rate = actual_failure_pct
                            else:
                                avg_error_rate = sum(error_values) / len(error_values)
                                error_rate = avg_error_rate * 100
                    else:
                        avg_error_rate = sum(error_values) / len(error_values)
                        error_rate = avg_error_rate * 100
        else:
            if error_key and error_key in error_metrics and count_key and count_key in count_metrics:
                error_values = error_metrics[error_key]
                count_value = count_metrics[count_key]
                
                if error_values and count_value > 0:
                    error_sum = sum(error_values)
                    error_count = len(error_values)
                    if error_count > 0:
                        avg_error_rate = error_sum / error_count
                        error_rate = avg_error_rate * 100
        
        if count_key and count_key in count_metrics:
            count_val = count_metrics[count_key]
            throughput = count_val / test_duration_mins if test_duration_mins > 0 else 0
        
        if avg is None and has_general_metrics:
            print(f"Menggunakan metrik umum untuk {step}")
            general_duration_values = metrics['http_req_duration']
            
            if general_duration_values:
                avg = sum(general_duration_values) / len(general_duration_values)
                min_val = min(general_duration_values)
                max_val = max(general_duration_values)
                
                variance = sum((x - avg) ** 2 for x in general_duration_values) / len(general_duration_values)
                std_dev = variance ** 0.5
            
            if 'http_req_failed' in error_metrics and error_metrics['http_req_failed']:
                error_rate = sum(error_metrics['http_req_failed']) / len(error_metrics['http_req_failed']) * 100
            
            if 'http_reqs' in count_metrics:
                count_val = count_metrics['http_reqs'] / len(steps)
                throughput = count_val / test_duration_mins if test_duration_mins > 0 else 0
        
        df.loc[i] = [
            step,
            format_number_id(avg) if avg is not None else "N/A",
            format_number_id(min_val) if min_val is not None else "N/A",
            format_number_id(max_val) if max_val is not None else "N/A",
            format_number_id(std_dev) if std_dev is not None else "N/A",
            format_number_id(error_rate, 1) if error_rate is not None else "0,0",
            format_number_id(throughput, 1) if throughput is not None else "N/A"
        ]
    
    if "contributor_workflow_duration" in metrics:
        workflow_values = metrics["contributor_workflow_duration"]
        if workflow_values:
            avg = sum(workflow_values) / len(workflow_values)
            min_val = min(workflow_values)
            max_val = max(workflow_values)
            
            variance = sum((x - avg) ** 2 for x in workflow_values) / len(workflow_values)
            std_dev = variance ** 0.5
            
            overall_error = None
            if 'http_req_failed' in error_metrics and error_metrics['http_req_failed']:
                overall_error = sum(error_metrics['http_req_failed']) / len(error_metrics['http_req_failed']) * 100
            
            throughput = count_metrics.get("iterations", 0) / test_duration_mins if test_duration_mins > 0 else 0
            
            df.loc[len(steps)] = [
                "Total Workflow",
                format_number_id(avg),
                format_number_id(min_val),
                format_number_id(max_val),
                format_number_id(std_dev),
                format_number_id(overall_error, 1) if overall_error is not None else "0,0",
                format_number_id(throughput, 1)
            ]
    
    return df

def save_results(df, test_time, prefix="contributor"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    csv_file = f"{prefix}_load_test_results_{timestamp}.csv"
    df.to_csv(csv_file, index=False)
    print(f"Hasil disimpan ke {csv_file}")
    
    word_file = f"{prefix}_load_test_results_word_{timestamp}.txt"
    with open(word_file, 'w') as f:
        f.write(df.to_string(index=False))
    print(f"Format untuk Word disimpan ke {word_file}")

def process_k6_results(json_file):
    metrics, count_metrics, error_metrics, test_duration_mins, test_time = parse_ndjson_k6_results(json_file)
    
    if metrics is None:
        print("Gagal memproses file. Program dihentikan.")
        return
    
    print("\nMetrik durasi yang tersedia:")
    for key in sorted(metrics.keys()):
        print(f"  - {key} ({len(metrics[key])} nilai)")
    
    print("\nMetrik error yang tersedia:")
    for key in sorted(error_metrics.keys()):
        print(f"  - {key} ({len(error_metrics[key])} nilai)")
    
    print("\nMetrik count yang tersedia:")
    for key in sorted(count_metrics.keys()):
        print(f"  - {key}: {count_metrics[key]}")
    
    df = prepare_data_table_contributor(metrics, count_metrics, error_metrics, test_duration_mins)
    
    print("\nTabel Performa UI Heritage - Alur Kontributor:")
    print("="*120)
    print(df.to_string(index=False))
    print("="*120)
    
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
        json_file = input("Masukkan path ke file hasil k6 untuk alur kontributor (NDJSON): ")
    
    process_k6_results(json_file)