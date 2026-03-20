/**
 * Feedback - Sistema de feedback visual (toasts, loaders, etc)
 */

// ============================================================
// TOAST NOTIFICATIONS
// ============================================================

class Toast {
    constructor(message, type = 'info', duration = 3000) {
        this.message = message;
        this.type = type; // 'success', 'error', 'warning', 'info'
        this.duration = duration;
        this.element = null;
    }

    show() {
        // Criar container se não existir
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                gap: 10px;
            `;
            document.body.appendChild(container);
        }

        // Criar elemento do toast
        this.element = document.createElement('div');
        this.element.className = `toast toast-${this.type}`;
        this.element.style.cssText = `
            background: ${this.getBackgroundColor()};
            color: white;
            padding: 12px 16px;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            min-width: 300px;
            animation: slideInRight 0.3s ease;
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 14px;
        `;

        // Adicionar ícone
        const icon = this.getIcon();
        if (icon) {
            const iconEl = document.createElement('span');
            iconEl.innerHTML = icon;
            iconEl.style.fontSize = '18px';
            this.element.appendChild(iconEl);
        }

        // Adicionar mensagem
        const msgEl = document.createElement('span');
        msgEl.textContent = this.message;
        this.element.appendChild(msgEl);

        // Adicionar botão de fechar
        const closeBtn = document.createElement('button');
        closeBtn.innerHTML = '✕';
        closeBtn.style.cssText = `
            background: none;
            border: none;
            color: white;
            cursor: pointer;
            font-size: 16px;
            margin-left: auto;
            padding: 0;
            opacity: 0.7;
            transition: opacity 0.2s;
        `;
        closeBtn.onmouseover = () => closeBtn.style.opacity = '1';
        closeBtn.onmouseout = () => closeBtn.style.opacity = '0.7';
        closeBtn.onclick = () => this.hide();
        this.element.appendChild(closeBtn);

        container.appendChild(this.element);

        // Auto-hide após duration
        if (this.duration > 0) {
            setTimeout(() => this.hide(), this.duration);
        }
    }

    hide() {
        if (this.element) {
            this.element.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => {
                if (this.element && this.element.parentNode) {
                    this.element.parentNode.removeChild(this.element);
                }
            }, 300);
        }
    }

    getBackgroundColor() {
        const colors = {
            'success': '#4caf50',
            'error': '#f44336',
            'warning': '#ff9800',
            'info': '#2196f3'
        };
        return colors[this.type] || colors['info'];
    }

    getIcon() {
        const icons = {
            'success': '✓',
            'error': '✕',
            'warning': '⚠',
            'info': 'ℹ'
        };
        return icons[this.type] || icons['info'];
    }
}

// Função global para mostrar toast
function toast(message, type = 'info', duration = 3000) {
    const t = new Toast(message, type, duration);
    t.show();
}

// ============================================================
// LOADING SPINNER
// ============================================================

class Loader {
    constructor(message = 'Carregando...') {
        this.message = message;
        this.element = null;
        this.overlay = null;
    }

    show() {
        // Criar overlay
        this.overlay = document.createElement('div');
        this.overlay.id = 'loader-overlay';
        this.overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9998;
            animation: fadeIn 0.3s ease;
        `;

        // Criar container do loader
        this.element = document.createElement('div');
        this.element.style.cssText = `
            background: white;
            padding: 30px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        `;

        // Adicionar spinner
        const spinner = document.createElement('div');
        spinner.style.cssText = `
            width: 50px;
            height: 50px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #2196f3;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        `;
        this.element.appendChild(spinner);

        // Adicionar mensagem
        const msg = document.createElement('p');
        msg.textContent = this.message;
        msg.style.cssText = `
            margin: 0;
            color: #333;
            font-size: 14px;
        `;
        this.element.appendChild(msg);

        this.overlay.appendChild(this.element);
        document.body.appendChild(this.overlay);
    }

    hide() {
        if (this.overlay) {
            this.overlay.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => {
                if (this.overlay && this.overlay.parentNode) {
                    this.overlay.parentNode.removeChild(this.overlay);
                }
            }, 300);
        }
    }
}

// Função global para mostrar loader
function showLoader(message = 'Carregando...') {
    const loader = new Loader(message);
    loader.show();
    return loader;
}

// ============================================================
// BUTTON LOADING STATE
// ============================================================

class ButtonLoader {
    constructor(buttonElement) {
        this.button = buttonElement;
        this.originalText = buttonElement.textContent;
        this.originalHTML = buttonElement.innerHTML;
        this.isLoading = false;
    }

    start(message = 'Carregando...') {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.button.disabled = true;
        this.button.style.opacity = '0.6';
        this.button.style.cursor = 'not-allowed';
        
        // Adicionar spinner inline
        this.button.innerHTML = `
            <span style="display: inline-block; width: 14px; height: 14px; border: 2px solid #fff; border-top-color: transparent; border-radius: 50%; animation: spin 0.8s linear infinite; margin-right: 8px;"></span>
            ${message}
        `;
    }

    stop() {
        if (!this.isLoading) return;
        
        this.isLoading = false;
        this.button.disabled = false;
        this.button.style.opacity = '1';
        this.button.style.cursor = 'pointer';
        this.button.innerHTML = this.originalHTML;
    }

    success(message = 'Sucesso!', duration = 2000) {
        this.button.innerHTML = `✓ ${message}`;
        this.button.style.background = '#4caf50';
        
        setTimeout(() => {
            this.button.style.background = '';
            this.button.innerHTML = this.originalHTML;
            this.isLoading = false;
        }, duration);
    }

    error(message = 'Erro!', duration = 2000) {
        this.button.innerHTML = `✕ ${message}`;
        this.button.style.background = '#f44336';
        
        setTimeout(() => {
            this.button.style.background = '';
            this.button.innerHTML = this.originalHTML;
            this.isLoading = false;
            this.button.disabled = false;
        }, duration);
    }
}

// ============================================================
// ANIMATIONS (CSS)
// ============================================================

// Adicionar estilos de animação
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    @keyframes slideInRight {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }

    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    @keyframes fadeOut {
        from { opacity: 1; }
        to { opacity: 0; }
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    .skeleton {
        background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
        background-size: 200% 100%;
        animation: pulse 1.5s infinite;
    }
`;
document.head.appendChild(style);

// ============================================================
// MODAL DIALOG
// ============================================================

class Modal {
    constructor(title, content, buttons = []) {
        this.title = title;
        this.content = content;
        this.buttons = buttons;
        this.element = null;
        this.overlay = null;
    }

    show() {
        // Criar overlay
        this.overlay = document.createElement('div');
        this.overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9997;
        `;

        // Criar modal
        this.element = document.createElement('div');
        this.element.style.cssText = `
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            max-width: 500px;
            width: 90%;
            animation: slideInRight 0.3s ease;
        `;

        // Header
        const header = document.createElement('div');
        header.style.cssText = `
            padding: 20px;
            border-bottom: 1px solid #eee;
            font-size: 18px;
            font-weight: 600;
            color: #333;
        `;
        header.textContent = this.title;
        this.element.appendChild(header);

        // Content
        const contentEl = document.createElement('div');
        contentEl.style.cssText = `
            padding: 20px;
            color: #666;
            font-size: 14px;
            line-height: 1.6;
        `;
        if (typeof this.content === 'string') {
            contentEl.textContent = this.content;
        } else {
            contentEl.appendChild(this.content);
        }
        this.element.appendChild(contentEl);

        // Footer com botões
        if (this.buttons.length > 0) {
            const footer = document.createElement('div');
            footer.style.cssText = `
                padding: 15px 20px;
                border-top: 1px solid #eee;
                display: flex;
                gap: 10px;
                justify-content: flex-end;
            `;

            this.buttons.forEach(btn => {
                const button = document.createElement('button');
                button.textContent = btn.text;
                button.style.cssText = `
                    padding: 8px 16px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: 500;
                    transition: all 0.2s;
                    ${btn.primary ? 'background: #2196f3; color: white;' : 'background: #f0f0f0; color: #333;'}
                `;
                button.onmouseover = () => {
                    button.style.opacity = '0.8';
                };
                button.onmouseout = () => {
                    button.style.opacity = '1';
                };
                button.onclick = () => {
                    if (btn.callback) btn.callback();
                    this.hide();
                };
                footer.appendChild(button);
            });

            this.element.appendChild(footer);
        }

        this.overlay.appendChild(this.element);
        document.body.appendChild(this.overlay);

        // Fechar ao clicar no overlay
        this.overlay.onclick = (e) => {
            if (e.target === this.overlay) {
                this.hide();
            }
        };
    }

    hide() {
        if (this.overlay) {
            this.overlay.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => {
                if (this.overlay && this.overlay.parentNode) {
                    this.overlay.parentNode.removeChild(this.overlay);
                }
            }, 300);
        }
    }
}

// ============================================================
// CONFIRM DIALOG
// ============================================================

function confirm(title, message, onConfirm, onCancel) {
    const modal = new Modal(title, message, [
        { text: 'Cancelar', callback: onCancel },
        { text: 'Confirmar', primary: true, callback: onConfirm }
    ]);
    modal.show();
}
