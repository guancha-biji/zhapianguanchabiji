import os
import sqlite3
import csv

# ==========================================
# 📁 路徑設定
# ==========================================
project_dir = r"C:\Users\Administrator\Documents\Publii\sites\zha-pian-guan-cha-bi-ji"
db_path = os.path.join(project_dir, "input", "db.sqlite")
csv_path = os.path.join(project_dir, "indexed_urls.csv")

def load_indexed_slugs():
    """從 GSC 匯出的 CSV 中提取已經被收錄的 slug/網址白名單"""
    indexed_slugs = set()
    if not os.path.exists(csv_path):
        print(f"⚠️ 找不到 CSV 檔案: {csv_path}")
        return indexed_slugs

    try:
        with open(csv_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            for row in reader:
                for col in row:
                    # 從網址中萃取出 slug (例如 https://scamobserver.org/abc-scam/ -> abc-scam)
                    match = re_slug_extract(col)
                    if match:
                        indexed_slugs.add(match)
    except Exception as e:
        print(f"⚠️ 讀取 CSV 發生錯誤: {e}")
    
    print(f"🛡️ 成功載入已收錄（受保護）的網址 slug 共 {len(indexed_slugs)} 個")
    return indexed_slugs

def re_slug_extract(text):
    """輔助函數：從網址字串中抓取最後的路徑作為 slug"""
    parts = [p for p in text.strip('/').split('/') if p]
    if parts:
        return parts[-1]
    return None

def clean_duplicates():
    if not os.path.exists(db_path):
        print(f"❌ 找不到 Publii 資料庫: {db_path}")
        return

    protected_slugs = load_indexed_slugs()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 取得所有文章
    cursor.execute("SELECT id, title, slug FROM posts")
    posts = cursor.fetchall()
    
    print(f"📚 資料庫目前總文章數: {len(posts)} 篇")
    
    seen_platforms = set()
    deleted_count = 0
    protected_count = 0

    for post_id, title, slug in posts:
        # 簡化識別碼，用來判斷是否為同一個平台的重複文章
        # 例如將 scam-165-trend-03 或是 abc-scam-2 簡化為主體名稱
        base_name = slug.split('-scam')[0].split('-trend')[0].strip('-')
        
        is_indexed = slug in protected_slugs

        if base_name in seen_platforms:
            # 發現重複平台！
            if is_indexed:
                print(f"🛡️ 【受保護・略過】《{title}》 (slug: {slug}) 雖然重複，但已在 GSC 收錄中，安全保留！")
                protected_count += 1
            else:
                print(f"🗑️ 【安全刪除】《{title}》 (slug: {slug}) 屬重複且未被收錄，正在從資料庫清除...")
                cursor.execute("DELETE FROM posts WHERE id = ?", (post_id,))
                cursor.execute("DELETE FROM posts_tags WHERE post_id = ?", (post_id,))
                deleted_count += 1
        else:
            seen_platforms.add(base_name)

    conn.commit()
    conn.close()

    print("\n" + "="*40)
    print(f"🎉 清理完畢！")
    print(f"🗑️ 總共刪除未收錄的重複文章: {deleted_count} 篇")
    print(f"🛡️ 因為已收錄而安全保護的重複文章: {protected_count} 篇")
    print("="*40)

if __name__ == "__main__":
    clean_duplicates()