import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import time
import threading
import pytz
from logistic import LogisticsOptimizer  # 导入之前的算法核心

# 初始化系统状态
def init_system():

    if 'optimizer' not in st.session_state:
        st.session_state.optimizer = LogisticsOptimizer(
            factory_location=(31.2304, 121.4737))
    if 'running' not in st.session_state:
        st.session_state.running = False
    if 'last_update' not in st.session_state:
        st.session_state.last_update = datetime.now(pytz.utc)

# 实时数据看板
def display_dashboard():

    st.title("🚚 Routing Map ")    

    with st.sidebar:
        st.header("报警设置")
        delay_threshold = st.number_input("延迟报警阈值（分钟）", 30)
        load_threshold = st.slider("负载率阈值", 0.0, 1.0, 0.8)
    # 创建三列布局
    col1, col2, col3 = st.columns([3, 2, 1])
    
 
    with col1:
        # 地图展示
        st.subheader("实时位置")
        update_map()
    
    with col2:
        # 生产监控
        st.subheader("🏭 文件上传")
        display_production()
        
        # 事件通知
        st.subheader("⚠️ 位置信息")
        display_events()
    
    with col3:
        # 车辆状态
        st.subheader("🚛 路由计算")
        display_vehicles()
        
        # 系统控制面板
        # st.subheader("⚙️ 系统控制")
        # st.button("▶️ 启动优化" if not st.session_state.running else "⏹️ 停止优化",
        #          on_click=toggle_optimization)

# 地图组件
def update_map():
    try:
        import pydeck as pdk
        
        vehicle_data = [{
            "coordinates": v['position'][::-1],  # 转换为[lng, lat]
            "color": [52, 152, 219],
            "radius": 50
        } for v in st.session_state.get('vehicles', [])]
        
        st.pydeck_chart(pdk.Deck(
            map_style='road',
            initial_view_state=pdk.ViewState(
                latitude=31.2304,
                longitude=121.4737,
                zoom=12,
                pitch=50
            ),
            layers=[
                pdk.Layer(
                    'ScatterplotLayer',
                    data=vehicle_data,
                    get_position='coordinates',
                    get_color='color',
                    get_radius='radius',
                    pickable=True
                )
            ]
        ))
    except Exception as e:
        st.error(f"地图加载失败: {str(e)}")

# 生产数据展示
def display_production():
    production = st.session_state.get('production', [])
    if production:
        st.bar_chart(
            {p['type']: p['amount'] for p in production},
            color='#3498db'
        )
        for p in production:
            st.caption(f"{p['type']}: {p['amount']}件")
    else:
        st.info("暂无生产数据")

# 车辆状态展示
def display_vehicles():
    vehicles = st.session_state.get('vehicles', [])
    for v in vehicles:
        progress = v['load'] / v['capacity']
        st.metric(
            label=f"车辆 {v['id']}",
            value=f"{v['load']}/{v['capacity']}",
            help=f"位置: {v['position']}"
        )
        st.progress(progress)

# 事件通知
def display_events():
    events = st.session_state.get('events', [])
    if events:
        for event in events[-3:]:  # 显示最近3条
            st.error(f"⚠️ {event['type']} @ {event['time']}")
    else:
        st.info("当前无待处理事件")

# 优化控制线程
def optimization_thread():
    while st.session_state.running:
        try:
            # 执行优化逻辑
            st.session_state.optimizer._update_data()
            
            # 更新共享数据
            current_time = datetime.now(pytz.utc)
            if (current_time - st.session_state.last_update).seconds >= 1:
                with st.session_state.optimizer.data_stream.lock:
                    # 更新车辆数据
                    st.session_state.vehicles = [
                        {
                            "id": v.id,
                            "position": v.position,
                            "load": v.current_load,
                            "capacity": v.capacity
                        }
                        for v in st.session_state.optimizer.data_stream.get_vehicle_states()
                    ]
                    
                    # 更新生产数据
                    st.session_state.production = [
                        {
                            "type": p.type,
                            "amount": p.amount
                        }
                        for p in st.session_state.optimizer.data_stream.get_hourly_production()
                    ]
                    
                    # 处理事件
                    new_events = st.session_state.optimizer.data_stream.events
                    if new_events:
                        st.session_state.events = [{
                            "type": e['type'],
                            "time": current_time.strftime("%H:%M:%S"),
                            "location": e['location']
                        } for e in new_events]
                        st.toast(f"新事件: {new_events[-1]['type']}", icon="⚠️")
                
                st.session_state.last_update = current_time
                time.sleep(0.5)
                
        except Exception as e:
            st.error(f"优化进程错误: {str(e)}")
            st.session_state.running = False

# 启动/停止优化
def toggle_optimization():
    st.session_state.running = not st.session_state.running
    if st.session_state.running:
        threading.Thread(target=optimization_thread, daemon=True).start()

# 主程序
if __name__ == "__main__":
    init_system()
    display_dashboard()
    
    # 自动刷新页面（每2秒）
    st_autorefresh(interval=2000, key="dashboard_refresh")
