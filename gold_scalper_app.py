import tkinter as tk
import MetaTrader5 as mt5
import threading
import time

class VeloxScalperEngine:
    def __init__(self, root):
        self.root = root
        self.root.title("VELOX Engine v1.0.0")
        self.root.geometry("340x460")
        self.root.configure(bg="#0D0D0D")
        self.root.resizable(False, False)

        self.symbol = "XAUUSD"
        self.lot_size = 0.01
        self.is_running = False

        # Init MT5 Linkage
        if not mt5.initialize():
            self.status = "DISCONNECTED"
            self.status_color = "#FF3333"
        else:
            self.status = "CONNECTED"
            self.status_color = "#00FF00"

        self.build_ui()
        
        # Start the background data thread loop
        threading.Thread(target=self.core_worker_loop, daemon=True).start()

    def build_ui(self):
        # Header banner text
        tk.Label(self.root, text="VELOX GOLD SCALPER PANEL", font=("Arial", 12, "bold"), fg="#00FF00", bg="#0D0D0D").pack(pady=15)
        
        # Dashboard box container
        self.box = tk.Frame(self.root, bg="#141414", bd=1, relief="solid", highlightbackground="#2A2A2A", highlightthickness=1)
        self.box.pack(fill="both", expand=True, padx=20, pady=5)

        # UI metrics labels
        self.lbl_mt5 = self.add_metric("MetaTrader 5 Client:", self.status, self.status_color)
        self.lbl_signal = self.add_metric("Predicted Action:", "IDLE", "#FFFFFF")
        self.lbl_balance = self.add_metric("Current Balance:", "$0.00", "#FFD700")
        self.lbl_equity = self.add_metric("Floating Equity:", "$0.00", "#FFFFFF")
        self.lbl_profit = self.add_metric("Floating Profit:", "$0.00", "#00FF00")
        self.lbl_ai = self.add_metric("AI Pipeline Matrix:", "ON (Acc=50%)", "#00FFFF")

        # Visual line divider
        tk.Frame(self.box, height=1, bg="#2A2A2A").pack(fill="x", padx=15, pady=15)

        # Interactive Control Buttons
        btn_layout = tk.Frame(self.box, bg="#141414")
        btn_layout.pack(pady=5)

        self.btn_power = tk.Button(btn_layout, text="START ENGINE", font=("Arial", 9, "bold"), bg="#222222", fg="#00FF00", width=13, relief="flat", command=self.toggle_engine)
        self.btn_power.grid(row=0, column=0, padx=5)

        btn_panic = tk.Button(btn_layout, text="PANIC CLOSE", font=("Arial", 9, "bold"), bg="#D93838", fg="#FFFFFF", width=13, relief="flat", command=self.nuke_positions)
        btn_panic.grid(row=0, column=1, padx=5)

    def add_metric(self, text_title, text_val, val_color):
        row = tk.Frame(self.box, bg="#141414")
        row.pack(fill="x", padx=15, pady=5)
        tk.Label(row, text=text_title, font=("Arial", 9), fg="#888888", bg="#141414").pack(side="left")
        lbl = tk.Label(row, text=text_val, font=("Arial", 9, "bold"), fg=val_color, bg="#141414")
        lbl.pack(side="right")
        return lbl

    def toggle_engine(self):
        self.is_running = not self.is_running
        if self.is_running:
            self.btn_power.config(text="STOP ENGINE", bg="#FF9900", fg="#000000")
        else:
            self.btn_power.config(text="START ENGINE", bg="#222222", fg="#00FF00")

    def run_trading_strategy(self):
        """ This is your core strategy block. Replace with your AI indicators. """
        if not self.is_running:
            return "OFF"
        
        # Scalping strategy framework fallback check:
        tick = mt5.symbol_info_tick(self.symbol)
        if tick:
            return "BUY" if tick.ask < tick.bid + 0.02 else "SELL"
        return "WAITING"

    def core_worker_loop(self):
        while True:
            if mt5.initialize():
                account = mt5.account_info()
                if account:
                    self.lbl_balance.config(text=f"${account.balance:,.2f}")
                    self.lbl_equity.config(text=f"${account.equity:,.2f}")
                    p_color = "#00FF00" if account.profit >= 0 else "#FF3333"
                    self.lbl_profit.config(text=f"${account.profit:,.2f}", fg=p_color)

                signal = self.run_trading_strategy()
                s_color = "#00FFFF" if signal == "BUY" else ("#FF3333" if signal == "SELL" else "#FFFFFF")
                self.lbl_signal.config(text=signal, fg=s_color)

                # Order Execution Guardrail
                if self.is_running and signal in ["BUY", "SELL"] and mt5.positions_total() == 0:
                    self.fire_market_order(signal)

            time.sleep(1.0)

    def fire_market_order(self, direction):
        order_type = mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(self.symbol).ask if direction == "BUY" else mt5.symbol_info_tick(self.symbol).bid
        
        req = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": self.lot_size,
            "type": order_type,
            "price": price,
            "deviation": 20,
            "magic": 77712,
            "comment": "Velox Cloud Update Engine",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        mt5.order_send(req)

    def nuke_positions(self):
        positions = mt5.positions_get(symbol=self.symbol)
        if positions:
            for p in positions:
                o_type = mt5.ORDER_TYPE_SELL if p.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(self.symbol).bid if p.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(self.symbol).ask
                close_req = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": self.symbol,
                    "volume": p.volume,
                    "type": o_type,
                    "position": p.ticket,
                    "price": price,
                    "deviation": 20,
                    "magic": 77712,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }
                mt5.order_send(close_req)

if __name__ == "__main__":
    root = tk.Tk()
    app = VeloxScalperEngine(root)
    root.mainloop()
    mt5.shutdown()
