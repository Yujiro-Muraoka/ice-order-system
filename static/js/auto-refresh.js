/**
 * cafeMuji 自動更新機能
 * 指定したDOM要素の数値が増加したタイミング、もしくは一定間隔で画面を再読み込みするヘルパー。
 *
 * 想定ユースケース:
 *   - キッチン/デシャップ画面で未完了件数が増えたら自動的に最新状態へ更新
 *   - 待ち時間表示画面のように、単純に n 秒ごとリロードしたいケース
 */

class AutoRefresh {
    constructor(options = {}) {
        /**
         * @property {number} interval - 更新チェックの間隔(ms)。デフォルトは 5 秒。
         */
        this.interval = options.interval || 5000; // 5秒間隔
        /**
         * @property {string} storageKey - 前回値を保存する localStorage キー。画面ごとに変えると競合しない。
         */
        this.storageKey = options.storageKey || 'auto_refresh_value';
        /**
         * @property {string} valueSelector - 監視対象となる要素の CSS セレクタ。
         *                                    `data-auto-refresh-value` 属性か textContent から値を取得する。
         */
        this.valueSelector = options.valueSelector || '[data-auto-refresh-value]';
        /**
         * @property {Function} parseValue - 要素から値を抽出する関数。画面ごとにフォーマットが違う場合に差し替える。
         */
        this.parseValue = options.parseValue || ((raw) => {
            if (raw === null || raw === undefined) {
                return null;
            }
            const text = String(raw);
            const match = text.match(/-?\d+(?:\.\d+)?/);
            return match ? Number(match[0]) : null;
        });
        /**
         * @property {boolean} reloadOnDecrease - 値が減少した際もリロードするかどうか。既定では true。
         *                                       待ち人数など増減を全て反映したい場合は true のまま。
         */
        this.reloadOnDecrease = options.reloadOnDecrease !== undefined ? options.reloadOnDecrease : true;
        /**
         * @property {boolean} forceReload - 値の差分チェックをせず、常に interval ごとにページをリロードする。
         *                                   待ち時間表示のように単純に周期リロードしたい画面で使用。
         */
        this.forceReload = options.forceReload || false;
        /**
         * @property {boolean} createButton - 右上の手動更新ボタンを表示するかどうか。
         *                                   ステータスモニタ画面では true、看板用画面では false にすることを推奨。
         */
        this.createButton = options.createButton !== undefined ? options.createButton : true;
        /**
         * @property {string} scrollStorageKey - スクロール位置保存に用いる localStorage キー。
         *                                      複数画面で同時使用する場合は上書きしないように変更可能。
         */
        this.scrollStorageKey = options.scrollStorageKey || 'scroll_position';
        /**
         * @property {?number} refreshTimer - setInterval の識別子。停止時にクリアする。
         */
        this.refreshTimer = null;
        /**
         * @property {boolean} isActive - ページがフォアグラウンドの場合のみチェックを行うためのフラグ。
         */
        this.isActive = true;

        this.prepareInitialValue();

        if (this.createButton) {
            this.createRefreshButton();
        }

        if (this.forceReload) {
            this.refreshTimer = setInterval(() => {
                this.refreshPage();
            }, this.interval);
            return;
        }

        this.start();
        this.setupVisibilityChange();
    }

    prepareInitialValue() {
        // 初回ロード時に監視対象の要素が存在すれば、その値を localStorage に保存しておく。
        // 他ページと storageKey が衝突している場合でも意図せずリロードされないよう、既に値があればスキップ。
        const element = document.querySelector(this.valueSelector);
        if (!element) {
            return;
        }
        const stored = localStorage.getItem(this.storageKey);
        if (stored !== null) {
            return;
        }
        const raw = element.getAttribute('data-auto-refresh-value') ?? element.textContent;
        const value = this.parseValue(raw, element);
        if (value !== null && !Number.isNaN(value)) {
            localStorage.setItem(this.storageKey, value.toString());
        }
    }

    /**
     * 手動更新ボタンを作成
     */
    createRefreshButton() {
        // 画面右上に手動更新ボタンを配置。必要に応じて createButton=false で非表示にできる。
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

    getStoredValue() {
        // localStorage から前回値を取得。数値文字列で保存しているため Number 化して返却。
        const stored = localStorage.getItem(this.storageKey);
        if (stored === null) {
            return null;
        }
        const num = Number(stored);
        return Number.isNaN(num) ? stored : num;
    }

    setStoredValue(value) {
        // null / undefined / NaN は無視し、正規の値のみ保存。
        if (value === null || value === undefined || Number.isNaN(value)) {
            return;
        }
        localStorage.setItem(this.storageKey, value.toString());
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

            if (!response.ok) {
                return;
            }

            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');

            const element = doc.querySelector(this.valueSelector);
            if (!element) {
                // 対象要素が見つからない場合はページ構造が変わったと判断しリロード。
                this.refreshPage();
                return;
            }

            const raw = element.getAttribute('data-auto-refresh-value') ?? element.textContent;
            const currentValue = this.parseValue(raw, element);

            if (currentValue === null || Number.isNaN(currentValue)) {
                // 値が取得できない場合もリロード。画面繰り返し読み込みで安定化させる。
                this.refreshPage();
                return;
            }

            const previousValue = this.getStoredValue();

            if (previousValue === null) {
                // 初回実行などで前回値が無い場合は保存だけ行い終了。
                this.setStoredValue(currentValue);
                return;
            }

            if (currentValue > previousValue || (this.reloadOnDecrease && currentValue !== previousValue)) {
                // 値が増加、または減少でも監視対象なら即リロード。
                this.setStoredValue(currentValue);
                this.refreshPage();
            } else if (currentValue !== previousValue) {
                // リロード条件を満たさない差分の場合でも値は更新しておく。
                this.setStoredValue(currentValue);
            }
        } catch (error) {
            console.error('自動更新チェックエラー:', error);
            this.refreshPage();
        }
    }

    /**
     * ページを更新
     */
    refreshPage() {
        // リロード前に現在のスクロール位置を保存し、復帰時に戻せるようにする。
        const scrollPosition = window.pageYOffset;
        localStorage.setItem(this.scrollStorageKey, scrollPosition.toString());

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
        // タブが非アクティブな間はネットワークリクエストを抑制し、戻ったタイミングで即チェックする。
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.isActive = false;
            } else {
                this.isActive = true;
                setTimeout(() => {
                    this.checkForUpdates();
                }, 1000);
            }
        });
    }

    /**
     * スクロール位置を復元
     */
    static restoreScrollPosition(key = 'scroll_position') {
        // 上記 refreshPage で保存したスクロール情報があれば復元し、その後ストレージから除去する。
        const scrollPosition = localStorage.getItem(key);
        if (scrollPosition) {
            window.scrollTo(0, parseInt(scrollPosition, 10));
            localStorage.removeItem(key);
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    AutoRefresh.restoreScrollPosition();
});

window.AutoRefresh = AutoRefresh;