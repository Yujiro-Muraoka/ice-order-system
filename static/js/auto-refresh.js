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
    this.interval = options.interval || 5000;
    this.valueSelector = options.valueSelector || '[data-auto-refresh-value]';
    this.scrollStorageKey = options.scrollStorageKey || 'auto_refresh_scroll_pos';
    this.pollUrl = options.pollUrl || null;
    this.forceReload = Boolean(options.forceReload);
    this.fallbackReloadMs = options.fallbackReloadMs || null; // hard reload even if value unchanged
    this.maxFailuresBeforeReload = options.maxFailuresBeforeReload || 3;
    this.failureCount = 0;
    this.parseValue =
      typeof options.parseValue === 'function'
        ? options.parseValue
        : this.defaultParseValue;
    this.isPolling = false;
    this.lastValue = this.parseValue(this.getCurrentValue());
    this.fallbackTimerId = null;

    this.init();
  }

  init() {
    window.addEventListener('load', () => this.restoreScrollPosition());
    this.start();
  }

  defaultParseValue(raw) {
    if (raw === null || raw === undefined || raw === '') {
      return null;
    }
    const numeric = Number(raw);
    return Number.isNaN(numeric) ? String(raw) : numeric;
  }

  getCurrentValue() {
    const el = document.querySelector(this.valueSelector);
    return el ? el.dataset.autoRefreshValue : null;
  }

  start() {
    if (this.forceReload) {
      this.timerId = setInterval(() => this.reloadPage(), this.interval);
      this.resetFallbackTimer();
      return;
    }

    this.timerId = setInterval(() => {
      void this.checkForUpdate();
    }, this.interval);
    this.resetFallbackTimer();
  }

  async checkForUpdate() {
    if (this.isPolling) {
      return;
    }
    this.isPolling = true;
    try {
      const latestValue = await this.fetchLatestValue();
      if (latestValue === null) {
        return;
      }
      this.failureCount = 0;
      this.resetFallbackTimer();
      if (this.lastValue === null) {
        this.lastValue = latestValue;
        return;
      }
      if (latestValue !== this.lastValue) {
        this.reloadPage();
      }
    } catch (error) {
      console.warn('AutoRefresh polling failed:', error);
      this.failureCount += 1;
      if (this.failureCount >= this.maxFailuresBeforeReload) {
        this.reloadPage();
      }
    } finally {
      this.isPolling = false;
    }
  }

  async fetchLatestValue() {
    if (!this.pollUrl) {
      return this.parseValue(this.getCurrentValue());
    }

    const response = await fetch(this.pollUrl, {
      cache: 'no-store',
      headers: {
        Accept: 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
      },
    });

    if (!response.ok) {
      throw new Error(`Polling responded with ${response.status}`);
    }

    const payload = await response.json();
    const raw =
      payload.value ??
      payload.refresh_value ??
      payload.refreshValue ??
      payload.active_order_total ??
      null;

    return this.parseValue(raw);
  }

  reloadPage() {
    sessionStorage.setItem(this.scrollStorageKey, window.scrollY.toString());
    this.clearFallbackTimer();
    window.location.reload();
  }

  restoreScrollPosition() {
    const savedPos = sessionStorage.getItem(this.scrollStorageKey);
    if (savedPos !== null) {
      window.scrollTo(0, parseInt(savedPos, 10));
      sessionStorage.removeItem(this.scrollStorageKey);
    }
  }

  static restoreScrollPosition(key = 'auto_refresh_scroll_pos') {
    const savedPos = sessionStorage.getItem(key);
    if (savedPos !== null) {
      window.scrollTo(0, parseInt(savedPos, 10));
      sessionStorage.removeItem(key);
    }
  }

  resetFallbackTimer() {
    this.clearFallbackTimer();
    if (this.fallbackReloadMs) {
      this.fallbackTimerId = setTimeout(() => this.reloadPage(), this.fallbackReloadMs);
    }
  }

  clearFallbackTimer() {
    if (this.fallbackTimerId) {
      clearTimeout(this.fallbackTimerId);
      this.fallbackTimerId = null;
    }
  }
}

window.AutoRefresh = AutoRefresh;
