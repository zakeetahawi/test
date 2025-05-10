import { useSnackbar } from '../components/core';

interface UpdateNotificationOptions {
  onUpdate?: () => void;
  onDismiss?: () => void;
}

export class UpdateNotification {
  private notification: HTMLDivElement | null = null;
  private options: UpdateNotificationOptions;

  constructor(options: UpdateNotificationOptions = {}) {
    this.options = options;
  }

  public show() {
    // Create notification element if it doesn't exist
    if (!this.notification) {
      this.notification = document.createElement('div');
      this.notification.className = 'update-notification';
      this.setupNotification();
    }

    // Add to document if not already there
    if (!document.body.contains(this.notification)) {
      document.body.appendChild(this.notification);
    }
  }

  public hide() {
    if (this.notification && this.notification.parentNode) {
      this.notification.parentNode.removeChild(this.notification);
      this.options.onDismiss?.();
    }
  }

  private setupNotification() {
    if (!this.notification) return;

    this.notification.innerHTML = `
      <div style="
        position: fixed;
        bottom: 24px;
        right: 24px;
        background: #fff;
        padding: 16px 24px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 9999;
        direction: rtl;
        font-family: 'Cairo', sans-serif;
        display: flex;
        align-items: center;
        gap: 16px;
        min-width: 300px;
      ">
        <div style="flex: 1">
          <div style="font-weight: 600; margin-bottom: 4px;">
            تحديث جديد متوفر
          </div>
          <div style="color: #666; font-size: 14px;">
            يرجى تحديث الصفحة للحصول على آخر التحسينات
          </div>
        </div>
        <div style="display: flex; gap: 8px;">
          <button
            onclick="document.querySelector('.update-notification')?.remove(); window.location.reload();"
            style="
              padding: 8px 16px;
              background: #3f51b5;
              color: white;
              border: none;
              border-radius: 4px;
              cursor: pointer;
              font-family: inherit;
            "
          >
            تحديث
          </button>
          <button
            onclick="document.querySelector('.update-notification')?.remove();"
            style="
              padding: 8px 16px;
              background: transparent;
              border: 1px solid #ddd;
              border-radius: 4px;
              cursor: pointer;
              font-family: inherit;
            "
          >
            لاحقاً
          </button>
        </div>
      </div>
    `;

    // Add event listeners
    const updateButton = this.notification.querySelector('button');
    if (updateButton) {
      updateButton.addEventListener('click', () => {
        this.options.onUpdate?.();
        this.hide();
      });
    }
  }
}

export const showUpdateAvailable = () => {
  const notification = new UpdateNotification({
    onUpdate: () => {
      window.location.reload();
    }
  });
  notification.show();
};
