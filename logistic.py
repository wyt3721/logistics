from datetime import datetime, timedelta
import pytz # type: ignore
import random
import time

# ================= 基础数据类定义 =================
class DeliveryDemand:
    def __init__(self, product_type, quantity, location, time_window):
        self.type = product_type
        self.quantity = quantity
        self.location = location
        self.time_window = time_window  # 元组(start_time, end_time)

class VehicleState:
    def __init__(self, vehicle_id, position, capacity, current_load, route):
        self.id = vehicle_id
        self.position = position  # (lat, lng)
        self.capacity = capacity
        self.current_load = current_load
        self.route = route

class FactoryProduction:
    def __init__(self, product_type, amount, production_time):
        self.type = product_type
        self.amount = amount
        self.timestamp = production_time

# ================= 数据接口定义 =================
class DataStream:
    def __init__(self):
        self.orders = OrderSystem()
        self.vehicles = TelematicsSystem()
        self.traffic = TrafficMonitor()
        self.weather = WeatherService()
        self.factory = FactorySystem()

    def preprocess(self):
        return {
            'orders': self.orders.get_latest(),
            'positions': self.vehicles.get_gps(),
            'congestion': self.traffic.get_levels(),
            'weather': self.weather.get_conditions()
        }

    def get_hourly_production(self):
        return self.factory.get_production()

    def get_pending_orders(self):
        return self.orders.get_pending()

    def get_vehicle_states(self):
        return self.vehicles.get_status()

    def has_event(self):
        return random.random() < 0.2

    def get_event(self):
        events = ['accident', 'traffic_jam', 'weather_alert', 'order_change']
        return {
            'type': random.choice(events),
            'location': (
                31.23 + random.uniform(-0.1, 0.1),
                121.47 + random.uniform(-0.1, 0.1)
            )
        }

# ================= 子系统实现 =================
class OrderSystem:
    def get_latest(self):
        now = datetime.now()
        return [
            DeliveryDemand(
                '常规订单', 
                200, 
                (31.235, 121.480),
                (
                    now + timedelta(hours=1),
                    now + timedelta(hours=3)
                )
            )
        ]

    def get_pending(self):
        return []

class TelematicsSystem:
    def get_gps(self):
        return [
            (31.2304 + random.uniform(-0.01, 0.01),
             121.4737 + random.uniform(-0.01, 0.01))
            for _ in range(3)
        ]

    def get_status(self):
        return [
            VehicleState(i, (31.23, 121.47), 1000, 500, [])
            for i in range(3)
        ]

class TrafficMonitor:
    def get_levels(self):
        return {'current': random.choice(['畅通', '缓行', '拥堵'])}

class WeatherService:
    def get_conditions(self):
        return {
            'weather': random.choice(['晴', '雨', '雾']),
            'road_condition': random.uniform(0.8, 1.0)
        }

class FactorySystem:
    def get_production(self):
        return [
            FactoryProduction(
                f'产品{chr(65+i)}', 
                random.randint(100,500),
                datetime.now(pytz.utc)
            )
            for i in range(2)
        ]

# ================= 优化算法核心 =================
class LogisticsOptimizer:
    def __init__(self, factory_location):
        self.data_stream = DataStream()
        self.factory_location = factory_location
        self.tz = pytz.timezone('Asia/Shanghai')
        self.last_optimization = datetime.now(self.tz)
        self.current_solution = Solution([])

    def _update_data(self):
        try:
            self.data_stream.preprocess()
        except Exception as e:
            print(f"数据更新异常: {str(e)}")

    def _hourly_trigger(self):
        current = datetime.now(self.tz)
        return (current - self.last_optimization).seconds >= 3600

    def realtime_optimization(self):
        try:
            while True:
                self._update_data()
                
                if self._hourly_trigger():
                    print(f"\n=== 整点优化触发 [{datetime.now(self.tz).strftime('%H:%M')}] ===")
                    self._hourly_reoptimization()
                    self.last_optimization = datetime.now(self.tz)
                
                if self.data_stream.has_event():
                    event = self.data_stream.get_event()
                    print(f"\n! 事件响应: {event['type']}@{event['location']}")
                    self.current_solution = Solution([f"调整路线@{event['location']}"])
                
                self._dispatch_commands()
                time.sleep(1)

        except KeyboardInterrupt:
            print("优化进程安全终止")

    def _hourly_reoptimization(self):
        new_production = self.data_stream.get_hourly_production()
        print(f"新生产货物: {[f'{p.type}x{p.amount}' for p in new_production]}")
        updated_demands = self._generate_demands()
        print(f"总配送需求: {len(updated_demands)}项")
        self.current_solution = Solution([f"路线{i}" for i in range(len(updated_demands)//3 +1)])

    def _generate_demands(self):
        current_time = datetime.now(self.tz)
        return [
            *self.data_stream.get_pending_orders(),
            *[
                self._create_demand(p, current_time)
                for p in self.data_stream.get_hourly_production()
                if p.timestamp > current_time - timedelta(minutes=55)
            ]
        ]

    def _create_demand(self, product, base_time):
        return DeliveryDemand(
            product_type=product.type,
            quantity=product.amount,
            location=self.factory_location,
            time_window=(
                base_time + timedelta(hours=1, minutes=15),
                base_time + timedelta(hours=4)
            )
        )

    def _dispatch_commands(self):
        if self.current_solution.routes:
            print(f"当前执行: {len(self.current_solution.routes)}条运输路线")

class Solution:
    def __init__(self, routes):
        self.routes = routes

if __name__ == "__main__":
    print("=== 物流管理系统启动 ===")
    optimizer = LogisticsOptimizer(factory_location=(31.2304, 121.4737))
    
    try:
        optimizer.realtime_optimization()
    except KeyboardInterrupt:
        print("系统已安全关闭")