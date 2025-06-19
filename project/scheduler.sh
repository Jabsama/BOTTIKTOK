#!/bin/bash
"""
TikTok Video Automation Scheduler
Orchestrates the complete pipeline: scrape → rank → bandit pick → build → upload
Runs as cron job with proper error handling and logging
"""

# Configuration
PROJECT_DIR="/home/ubuntu/project"
PYTHON_ENV="/home/ubuntu/project/venv/bin/python"
LOG_FILE="/home/ubuntu/project/logs/scheduler.log"
ERROR_LOG="/home/ubuntu/project/logs/error.log"
LOCK_FILE="/tmp/tiktok_scheduler.lock"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to log errors
log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$ERROR_LOG"
}

# Function to check if another instance is running
check_lock() {
    if [ -f "$LOCK_FILE" ]; then
        local pid=$(cat "$LOCK_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            log_message "Another instance is already running (PID: $pid). Exiting."
            exit 1
        else
            log_message "Stale lock file found. Removing."
            rm -f "$LOCK_FILE"
        fi
    fi
}

# Function to create lock file
create_lock() {
    echo $$ > "$LOCK_FILE"
}

# Function to remove lock file
remove_lock() {
    rm -f "$LOCK_FILE"
}

# Function to run Python script with error handling
run_python_script() {
    local script_name="$1"
    local script_path="$PROJECT_DIR/$script_name"
    
    log_message "Running $script_name..."
    
    if [ ! -f "$script_path" ]; then
        log_error "$script_name not found at $script_path"
        return 1
    fi
    
    cd "$PROJECT_DIR" || {
        log_error "Failed to change to project directory"
        return 1
    }
    
    if ! "$PYTHON_ENV" "$script_path"; then
        log_error "$script_name failed"
        return 1
    fi
    
    log_message "$script_name completed successfully"
    return 0
}

# Function to check system resources
check_resources() {
    # Check available disk space (need at least 1GB)
    local available_space=$(df "$PROJECT_DIR" | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 1048576 ]; then  # 1GB in KB
        log_error "Insufficient disk space. Available: ${available_space}KB"
        return 1
    fi
    
    # Check memory usage (warn if over 80%)
    local memory_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [ "$memory_usage" -gt 80 ]; then
        log_message "WARNING: High memory usage: ${memory_usage}%"
    fi
    
    return 0
}

# Function to cleanup old files
cleanup_old_files() {
    log_message "Cleaning up old files..."
    
    # Remove videos older than 7 days
    find "$PROJECT_DIR/output" -name "*.mp4" -mtime +7 -delete 2>/dev/null || true
    
    # Remove log files older than 30 days
    find "$(dirname "$LOG_FILE")" -name "*.log" -mtime +30 -delete 2>/dev/null || true
    
    # Clean up temporary files
    find "$PROJECT_DIR" -name "temp_*" -mtime +1 -delete 2>/dev/null || true
    find "$PROJECT_DIR" -name "*.tmp" -mtime +1 -delete 2>/dev/null || true
    
    log_message "Cleanup completed"
}

# Function to backup database
backup_database() {
    local backup_dir="$PROJECT_DIR/backups"
    local backup_file="$backup_dir/trends_$(date +%Y%m%d_%H%M%S).db"
    
    mkdir -p "$backup_dir"
    
    if [ -f "$PROJECT_DIR/trends.db" ]; then
        cp "$PROJECT_DIR/trends.db" "$backup_file"
        log_message "Database backed up to $backup_file"
        
        # Keep only last 7 backups
        ls -t "$backup_dir"/trends_*.db | tail -n +8 | xargs rm -f 2>/dev/null || true
    fi
}

# Function to check API credentials
check_credentials() {
    if [ -z "$TIKTOK_CLIENT_KEY" ] || [ -z "$TIKTOK_ACCESS_TOKEN" ]; then
        log_error "TikTok API credentials not set in environment"
        return 1
    fi
    return 0
}

# Function to send notification (optional)
send_notification() {
    local message="$1"
    local webhook_url="$DISCORD_WEBHOOK_URL"  # Optional Discord webhook
    
    if [ -n "$webhook_url" ]; then
        curl -H "Content-Type: application/json" \
             -X POST \
             -d "{\"content\":\"🤖 TikTok Bot: $message\"}" \
             "$webhook_url" 2>/dev/null || true
    fi
}

# Main execution function
main() {
    log_message "=== TikTok Automation Pipeline Started ==="
    
    # Check if another instance is running
    check_lock
    create_lock
    
    # Trap to ensure cleanup on exit
    trap remove_lock EXIT
    
    # Check system resources
    if ! check_resources; then
        log_error "System resource check failed"
        exit 1
    fi
    
    # Check API credentials
    if ! check_credentials; then
        log_error "Credential check failed"
        exit 1
    fi
    
    # Backup database before starting
    backup_database
    
    # Step 1: Scrape trending hashtags
    if ! run_python_script "scraper_trends.py"; then
        log_error "Trend scraping failed"
        send_notification "❌ Trend scraping failed"
        exit 1
    fi
    
    # Step 2: Rank trends
    if ! run_python_script "ranker.py"; then
        log_error "Trend ranking failed"
        send_notification "❌ Trend ranking failed"
        exit 1
    fi
    
    # Step 3: Select hashtag with bandit
    log_message "Running bandit selection..."
    cd "$PROJECT_DIR" || exit 1
    
    selected_hashtag=$("$PYTHON_ENV" -c "
from bandit import TrendBandit
bandit = TrendBandit()
hashtag = bandit.select_hashtag()
print(hashtag)
" 2>/dev/null)
    
    if [ -z "$selected_hashtag" ]; then
        log_error "Bandit selection failed"
        send_notification "❌ Hashtag selection failed"
        exit 1
    fi
    
    log_message "Selected hashtag: $selected_hashtag"
    
    # Step 4: Generate script
    log_message "Generating video script..."
    script_data=$("$PYTHON_ENV" -c "
import json
from build_prompt import PromptBuilder
builder = PromptBuilder()
script = builder.generate_script('$selected_hashtag')
builder.save_script_to_db(script)
print(json.dumps(script))
" 2>/dev/null)
    
    if [ -z "$script_data" ]; then
        log_error "Script generation failed"
        send_notification "❌ Script generation failed"
        exit 1
    fi
    
    log_message "Script generated successfully"
    
    # Step 5: Create video
    log_message "Creating video..."
    video_path=$("$PYTHON_ENV" -c "
import json
from build_video import TikTokVideoBuilder
script = json.loads('$script_data')
builder = TikTokVideoBuilder()
video_path = builder.create_video(script)
print(video_path)
" 2>/dev/null)
    
    if [ ! -f "$video_path" ]; then
        log_error "Video creation failed"
        send_notification "❌ Video creation failed"
        exit 1
    fi
    
    log_message "Video created: $video_path"
    
    # Step 6: Upload video
    log_message "Uploading video..."
    upload_result=$("$PYTHON_ENV" -c "
import json
from upload import TikTokUploader
script = json.loads('$script_data')
uploader = TikTokUploader()
result = uploader.upload_video('$video_path', script)
print(json.dumps(result))
" 2>/dev/null)
    
    if [ -z "$upload_result" ]; then
        log_error "Upload failed"
        send_notification "❌ Video upload failed"
        exit 1
    fi
    
    # Parse upload result
    upload_success=$(echo "$upload_result" | "$PYTHON_ENV" -c "
import json, sys
result = json.load(sys.stdin)
print('true' if result.get('success') else 'false')
")
    
    if [ "$upload_success" = "true" ]; then
        log_message "Video uploaded successfully"
        send_notification "✅ New video uploaded: $selected_hashtag"
    else
        upload_message=$(echo "$upload_result" | "$PYTHON_ENV" -c "
import json, sys
result = json.load(sys.stdin)
print(result.get('message', 'Unknown error'))
")
        log_message "Upload result: $upload_message"
        
        if echo "$upload_result" | grep -q "scheduled"; then
            send_notification "⏰ Video scheduled: $selected_hashtag"
        else
            send_notification "❌ Upload failed: $upload_message"
        fi
    fi
    
    # Step 7: Process any scheduled uploads
    log_message "Processing scheduled uploads..."
    "$PYTHON_ENV" -c "
from upload import TikTokUploader
uploader = TikTokUploader()
uploader.process_scheduled_uploads()
" 2>/dev/null || log_error "Scheduled upload processing failed"
    
    # Step 8: Viral Remix Pipeline (if enabled)
    log_message "Running viral remix pipeline..."
    "$PYTHON_ENV" -c "
from viral_remix import ViralRemixer
import json

remixer = ViralRemixer()
stats = remixer.get_remix_statistics()

# Check if we can create more remixes today
if stats['today']['remaining_slots'] > 0:
    print('Running viral remix...')
    
    # Fetch and select viral videos
    videos = remixer.fetch_top_videos()
    top_videos = remixer.reason_select(videos)
    
    if top_videos:
        # Transform and upload first video
        video_id = top_videos[0]['video_id']
        remix_path = remixer.transform_video(video_id)
        
        if remix_path:
            result = remixer.upload_remix(remix_path, top_videos[0])
            if result.get('success'):
                print(f'Remix uploaded successfully: {video_id}')
            else:
                print(f'Remix upload failed: {result.get(\"error\", \"Unknown error\")}')
        else:
            print('Remix transformation failed')
    else:
        print('No suitable videos found for remixing')
else:
    print(f'Remix limit reached: {stats[\"today\"][\"published\"]}/{stats[\"today\"][\"total\"]} today')
" 2>/dev/null || log_error "Viral remix processing failed"
    
    # Step 9: Cleanup
    cleanup_old_files
    
    # Final statistics
    log_message "Getting final statistics..."
    "$PYTHON_ENV" -c "
from upload import TikTokUploader
from ranker import TrendRanker
from bandit import TrendBandit

uploader = TikTokUploader()
ranker = TrendRanker()
bandit = TrendBandit()

upload_stats = uploader.get_upload_statistics()
bandit_stats = bandit.get_bandit_statistics()

print(f'Upload stats: {upload_stats[\"today\"][\"successful\"]}/{upload_stats[\"today\"][\"total\"]} today')
print(f'Bandit stats: {bandit_stats[\"total_decisions\"]} decisions, {bandit_stats[\"avg_reward\"]:.1f} avg reward')
" 2>/dev/null || true
    
    log_message "=== TikTok Automation Pipeline Completed ==="
}

# Handle script arguments
case "${1:-}" in
    "test")
        log_message "Running in test mode"
        check_resources
        check_credentials
        run_python_script "scraper_trends.py"
        ;;
    "cleanup")
        log_message "Running cleanup only"
        cleanup_old_files
        ;;
    "backup")
        log_message "Running backup only"
        backup_database
        ;;
    *)
        main
        ;;
esac
