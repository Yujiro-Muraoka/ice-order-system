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
    this.storageKey = options.storageKey || 'auto_refresh_last_value';
    this.interval = options.interval || 5000;
    this.valueSelector = options.valueSelector || '[data-auto-refresh-value]';
    this.scrollStorageKey = options.scrollStorageKey || 'auto_refresh_scroll_pos';
    this.init();
  }

  init() {
    // ページ読み込み時にスクロール位置を復元
    window.addEventListener('load', () => {
      const savedPos = sessionStorage.getItem(this.scrollStorageKey);
      if (savedPos !== null) {
        window.scrollTo(0, parseInt(savedPos, 10));
        sessionStorage.removeItem(this.scrollStorageKey);
      }
    });

    // 定期的に更新をチェック
    this.start();
  }

  getCurrentValue() {
    const el = document.querySelector(this.valueSelector);
    return el ? el.dataset.autoRefreshValue : null;
  }

  start() {
    const initialValue = this.getCurrentValue();
    if (initialValue !== null) {
      localStorage.setItem(this.storageKey, initialValue);
    }

    setInterval(() => {
      this.checkForUpdate();
    }, this.interval);
  }

  checkForUpdate() {
    const storedValue = localStorage.getItem(this.storageKey);
    const currentValue = this.getCurrentValue();

    // currentValueがnullでなく、かつstoredValueと異なる場合にリロード
    if (currentValue !== null && storedValue !== currentValue) {
      this.reloadPage();
    }
  }

  reloadPage() {
    // リロード前に現在のスクロール位置を保存
    sessionStorage.setItem(this.scrollStorageKey, window.scrollY.toString());
    // ページをリロード
    window.location.reload();
  }
}

document.addEventListener('DOMContentLoaded', () => {
  AutoRefresh.restoreScrollPosition();
});

window.AutoRefresh = AutoRefresh;