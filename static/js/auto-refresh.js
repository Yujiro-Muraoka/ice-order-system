/**
 * cafeMuji 自動更新機能
 * キッチン画面で新しい注文が入った際に自動でページを更新する
 */

class AutoRefresh {
    constructor(options = {}) {
        this.interval = options.interval || 5000; // 5秒間隔
        this.storageKey = options.storageKey || 'active_count';
        this.refreshTimer = null;
        this.isActive = true;
        
        // 手動更新ボタンを作成
        this.createRefreshButton();
        
        // 自動更新を開始
        this.start();
        
        // ページの可視性変更を監視
        this.setupVisibilityChange();
    }
    
    /**
     * 手動更新ボタンを作成
     */
    createRefreshButton() {
        const button = document.createElement('button');
        button.textContent = '🔄 手動更新';
        button.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            padding: 10px 15px;
            background-color: #2196F3;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            z-index: 1000;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        `;
        
        button.addEventListener('click', () => {
            this.manualRefresh();
        });
        
        document.body.appendChild(button);
    }
    
    /**
     * 自動更新を開始
     */
    start() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }
        
        this.refreshTimer = setInterval(() => {
            if (this.isActive) {
                this.checkForUpdates();
            }
        }, this.interval);
    }
    
    /**
     * 自動更新を停止
     */
    stop() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
    }
    
    /**
     * 更新チェック
     */
    async checkForUpdates() {
        try {
            const response = await fetch(window.location.href, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (response.ok) {
                const html = await response.text();
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                
                // 未完了オーダー数を取得
                const currentCountElement = doc.querySelector('p:contains("未完了オーダー数")') || 
                                          doc.querySelector('p[data-active-count]');
                
                if (currentCountElement) {
                    const currentCountText = currentCountElement.textContent;
                    const currentCount = parseInt(currentCountText.match(/\d+/)?.[0] || '0');
                    
                    const previousCount = parseInt(localStorage.getItem(this.storageKey) || '0');
                    
                    if (currentCount > previousCount) {
                        // 新しい注文が追加された
                        this.refreshPage();
                    } else if (currentCount !== previousCount) {
                        // 注文数が変更された
                        localStorage.setItem(this.storageKey, currentCount.toString());
                    }
                }
            }
        } catch (error) {
            console.error('自動更新チェックエラー:', error);
        }
    }
    
    /**
     * ページを更新
     */
    refreshPage() {
        // スクロール位置を保存
        const scrollPosition = window.pageYOffset;
        localStorage.setItem('scroll_position', scrollPosition.toString());
        
        // ページをリロード
        window.location.reload();
    }
    
    /**
     * 手動更新
     */
    manualRefresh() {
        this.refreshPage();
    }
    
    /**
     * ページの可視性変更を監視
     */
    setupVisibilityChange() {
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.isActive = false;
            } else {
                this.isActive = true;
                // ページが再表示されたら即座にチェック
                setTimeout(() => {
                    this.checkForUpdates();
                }, 1000);
            }
        });
    }
    
    /**
     * スクロール位置を復元
     */
    static restoreScrollPosition() {
        const scrollPosition = localStorage.getItem('scroll_position');
        if (scrollPosition) {
            window.scrollTo(0, parseInt(scrollPosition));
            localStorage.removeItem('scroll_position');
        }
    }
}

// ページ読み込み時にスクロール位置を復元
document.addEventListener('DOMContentLoaded', () => {
    AutoRefresh.restoreScrollPosition();
});

// グローバルに公開
window.AutoRefresh = AutoRefresh;