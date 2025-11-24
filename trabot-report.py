"""
Trading Session Report Viewer
Beautiful GUI to view and analyze trading session JSON reports
Run with: streamlit run report_viewer.py
"""

import streamlit as st
import json
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Configuration
REPORTS_DIR = 'trading_reports'

# Page configuration
st.set_page_config(
    page_title="Trading Session Reports",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 1rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .profit-positive {
        color: #00ff00;
        font-weight: bold;
    }
    .profit-negative {
        color: #ff4444;
        font-weight: bold;
    }
    .stat-box {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


def load_session_files():
    """Load all JSON session files from the reports directory"""
    if not os.path.exists(REPORTS_DIR):
        return []
    
    files = []
    for filename in os.listdir(REPORTS_DIR):
        if filename.endswith('.json') and filename.startswith('session_'):
            filepath = os.path.join(REPORTS_DIR, filename)
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    files.append({
                        'filename': filename,
                        'filepath': filepath,
                        'data': data,
                        'session_id': data.get('session_id', 'Unknown'),
                        'start_time': data.get('start_time', 'Unknown'),
                        'total_profit_loss': data.get('total_profit_loss', 0)
                    })
            except Exception as e:
                st.sidebar.error(f"Error loading {filename}: {e}")
    
    # Sort by start time (newest first)
    files.sort(key=lambda x: x['start_time'], reverse=True)
    return files


def format_currency(amount):
    """Format currency with color"""
    if amount > 0:
        return f'<span class="profit-positive">${amount:,.2f}</span>'
    elif amount < 0:
        return f'<span class="profit-negative">${amount:,.2f}</span>'
    else:
        return f'${amount:,.2f}'


def display_session_overview(session_data):
    """Display overview of a trading session"""
    st.markdown('<h1 class="main-header">📊 Trading Session Report</h1>', unsafe_allow_html=True)
    
    # Session Info
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Session ID", session_data.get('session_id', 'N/A'))
    with col2:
        st.metric("Account Type", session_data.get('account_type', 'N/A'))
    with col3:
        st.metric("Timezone", session_data.get('timezone', 'N/A'))
    with col4:
        duration = session_data.get('duration', {}).get('formatted', 'N/A')
        st.metric("Duration", duration)
    
    st.divider()
    
    # Financial Summary
    st.subheader("💰 Financial Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    initial = session_data.get('initial_balance', 0)
    final = session_data.get('final_balance', 0)
    profit_loss = session_data.get('total_profit_loss', 0)
    roi = ((profit_loss / initial) * 100) if initial > 0 else 0
    
    with col1:
        st.metric("Initial Balance", f"${initial:,.2f}")
    with col2:
        st.metric("Final Balance", f"${final:,.2f}")
    with col3:
        st.metric("Total P/L", f"${profit_loss:,.2f}", 
                 delta=f"{roi:+.2f}%")
    with col4:
        roi_emoji = "📈" if profit_loss > 0 else "📉" if profit_loss < 0 else "➖"
        st.metric(f"{roi_emoji} ROI", f"{roi:+.2f}%")
    
    st.divider()


def display_statistics(session_data):
    """Display trading statistics"""
    stats = session_data.get('statistics', {})
    
    st.subheader("📈 Trading Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Trade Summary**")
        st.metric("Total Trades", stats.get('total_trades', 0))
        st.metric("Winning Trades", stats.get('winning_trades', 0))
        st.metric("Losing Trades", stats.get('losing_trades', 0))
        st.metric("Doji Trades", stats.get('doji_trades', 0))
    
    with col2:
        st.markdown("**Performance Metrics**")
        win_rate = stats.get('win_rate', 0)
        st.metric("Win Rate", f"{win_rate:.2f}%")
        st.metric("Largest Win", f"${stats.get('largest_win', 0):.2f}")
        st.metric("Largest Loss", f"${stats.get('largest_loss', 0):.2f}")
        avg_win = stats.get('average_profit_per_win', 0)
        st.metric("Avg Profit/Win", f"${avg_win:.2f}")
    
    with col3:
        st.markdown("**Cycle Statistics** (Martingale)")
        st.metric("Total Cycles", stats.get('total_cycles', 0))
        st.metric("Successful Cycles", stats.get('successful_cycles', 0))
        st.metric("Failed Cycles", stats.get('failed_cycles', 0))
        cycle_success = 0
        if stats.get('total_cycles', 0) > 0:
            cycle_success = (stats.get('successful_cycles', 0) / stats.get('total_cycles', 0)) * 100
        st.metric("Cycle Success Rate", f"{cycle_success:.2f}%")


def display_trades_table(session_data):
    """Display trades in a table"""
    trades = session_data.get('trades', [])
    
    if not trades:
        st.info("No trades recorded in this session")
        return
    
    st.subheader("📋 Trade History")
    
    # Convert to DataFrame
    df = pd.DataFrame(trades)
    
    # Select and rename columns for display
    display_columns = {
        'trade_number': 'Trade #',
        'timestamp': 'Time',
        'asset': 'Asset',
        'action': 'Action',
        'bet_amount': 'Bet',
        'duration': 'Duration (s)',
        'result': 'Result',
        'profit': 'Profit/Loss',
        'balance_after': 'Balance'
    }
    
    df_display = df[list(display_columns.keys())].copy()
    df_display.columns = list(display_columns.values())
    
    # Format numeric columns
    df_display['Bet'] = df_display['Bet'].apply(lambda x: f"${x:.2f}")
    df_display['Profit/Loss'] = df_display['Profit/Loss'].apply(lambda x: f"${x:+.2f}")
    df_display['Balance'] = df_display['Balance'].apply(lambda x: f"${x:.2f}")
    
    # Color code results
    def color_result(val):
        if val == 'WIN':
            return 'background-color: #d4edda'
        elif val == 'LOSS':
            return 'background-color: #f8d7da'
        else:
            return 'background-color: #fff3cd'
    
    styled_df = df_display.style.applymap(color_result, subset=['Result'])
    
    st.dataframe(styled_df, use_container_width=True, height=400)


def display_charts(session_data):
    """Display interactive charts"""
    trades = session_data.get('trades', [])
    
    if not trades:
        return
    
    st.subheader("📊 Visual Analysis")
    
    # Create DataFrame
    df = pd.DataFrame(trades)
    
    tab1, tab2, tab3, tab4 = st.tabs(["Balance Over Time", "Win/Loss Distribution", "Profit by Trade", "Asset Performance"])
    
    with tab1:
        # Balance progression chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(1, len(df) + 1)),
            y=df['balance_after'],
            mode='lines+markers',
            name='Balance',
            line=dict(color='#667eea', width=3),
            marker=dict(size=8),
            fill='tozeroy',
            fillcolor='rgba(102, 126, 234, 0.1)'
        ))
        
        # Add initial balance line
        initial_balance = session_data.get('initial_balance', 0)
        fig.add_hline(y=initial_balance, line_dash="dash", 
                     line_color="gray", annotation_text="Initial Balance")
        
        fig.update_layout(
            title="Balance Progression",
            xaxis_title="Trade Number",
            yaxis_title="Balance ($)",
            height=400,
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # Win/Loss pie chart
        result_counts = df['result'].value_counts()
        
        colors = {'WIN': '#28a745', 'LOSS': '#dc3545', 'DOJI': '#ffc107'}
        color_list = [colors.get(result, '#6c757d') for result in result_counts.index]
        
        fig = go.Figure(data=[go.Pie(
            labels=result_counts.index,
            values=result_counts.values,
            marker=dict(colors=color_list),
            hole=0.4,
            textinfo='label+percent+value',
            textfont_size=14
        )])
        
        fig.update_layout(
            title="Trade Results Distribution",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        # Profit/Loss by trade
        colors = ['green' if x > 0 else 'red' if x < 0 else 'gray' for x in df['profit']]
        
        fig = go.Figure(data=[go.Bar(
            x=list(range(1, len(df) + 1)),
            y=df['profit'],
            marker_color=colors,
            text=df['profit'].apply(lambda x: f"${x:+.2f}"),
            textposition='outside'
        )])
        
        fig.update_layout(
            title="Profit/Loss per Trade",
            xaxis_title="Trade Number",
            yaxis_title="Profit/Loss ($)",
            height=400,
            showlegend=False
        )
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        # Performance by asset
        asset_stats = df.groupby('asset').agg({
            'profit': 'sum',
            'trade_number': 'count'
        }).reset_index()
        asset_stats.columns = ['Asset', 'Total Profit', 'Trades']
        
        fig = go.Figure(data=[go.Bar(
            x=asset_stats['Asset'],
            y=asset_stats['Total Profit'],
            marker_color=['green' if x > 0 else 'red' for x in asset_stats['Total Profit']],
            text=asset_stats['Total Profit'].apply(lambda x: f"${x:+.2f}"),
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Profit: $%{y:.2f}<br>Trades: %{customdata}<extra></extra>',
            customdata=asset_stats['Trades']
        )])
        
        fig.update_layout(
            title="Total Profit/Loss by Asset",
            xaxis_title="Asset",
            yaxis_title="Total Profit/Loss ($)",
            height=400
        )
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        st.plotly_chart(fig, use_container_width=True)


def display_cycles(session_data):
    """Display martingale cycle information"""
    cycles = session_data.get('cycles', [])
    
    if not cycles:
        st.info("No cycle data available (not using strategy or session incomplete)")
        return
    
    st.subheader("🎯 Martingale Cycles")
    
    for cycle in cycles:
        cycle_num = cycle.get('cycle_number', 0)
        result = cycle.get('result', 'UNKNOWN')
        profit = cycle.get('profit_loss', 0)
        trades_count = cycle.get('trades_in_cycle', 0)
        
        # Color code based on result
        if result == 'WIN':
            emoji = "✅"
            color = "green"
        else:
            emoji = "❌"
            color = "red"
        
        with st.expander(f"{emoji} Cycle #{cycle_num} - {result} - ${profit:+.2f} ({trades_count} trades)"):
            cycle_trades = cycle.get('trades', [])
            if cycle_trades:
                cycle_df = pd.DataFrame(cycle_trades)
                
                # Display cycle trades
                display_cols = ['trade_number', 'timestamp', 'action', 'bet_amount', 'result', 'profit']
                cycle_df_display = cycle_df[display_cols].copy()
                cycle_df_display.columns = ['Trade #', 'Time', 'Action', 'Bet', 'Result', 'Profit']
                cycle_df_display['Bet'] = cycle_df_display['Bet'].apply(lambda x: f"${x:.2f}")
                cycle_df_display['Profit'] = cycle_df_display['Profit'].apply(lambda x: f"${x:+.2f}")
                
                st.dataframe(cycle_df_display, use_container_width=True)
                
                # Cycle summary
                st.markdown(f"""
                **Cycle Summary:**
                - Total trades in cycle: {trades_count}
                - Final result: **{result}**
                - Net profit/loss: **${profit:+.2f}**
                """)


def display_events(session_data):
    """Display session events timeline"""
    events = session_data.get('events', [])
    
    if not events:
        st.info("No events logged")
        return
    
    st.subheader("📅 Session Events Timeline")
    
    for event in events:
        event_type = event.get('type', 'UNKNOWN')
        timestamp = event.get('timestamp', 'N/A')
        description = event.get('description', 'No description')
        
        # Choose emoji based on event type
        emoji_map = {
            'SESSION_START': '🚀',
            'SESSION_END': '🏁',
            'AUTO_TRADE_START': '▶️',
            'TELEGRAM_CONNECTED': '📱',
            'QUOTEX_CONNECTED': '🔌',
            'TRADE_FAILED': '❌',
            'TRADE_ERROR': '⚠️',
            'CYCLE_BLOWN': '💥',
            'COMMAND_ERROR': '🐛'
        }
        emoji = emoji_map.get(event_type, '📌')
        
        with st.expander(f"{emoji} {timestamp} - {event_type}"):
            st.write(f"**Description:** {description}")
            details = event.get('details', {})
            if details:
                st.json(details)


def display_strategy_config(session_data):
    """Display strategy configuration"""
    strategy = session_data.get('strategy_config', {})
    
    st.subheader("⚙️ Strategy Configuration")
    
    if strategy.get('enabled', False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Strategy", "Triple Martingale ✅")
        with col2:
            st.metric("Initial Stake", f"${strategy.get('initial_stake', 0):.2f}")
        with col3:
            st.metric("Max Chances", strategy.get('max_chances', 0))
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Strategy", "Fixed Amount ❌")
        with col2:
            st.metric("Trade Amount", f"${strategy.get('default_amount', 0):.2f}")


def main():
    """Main application"""
    
    # Sidebar - Session Selection
    st.sidebar.title("📂 Session Reports")
    
    # Load all sessions
    sessions = load_session_files()
    
    if not sessions:
        st.sidebar.warning(f"No session reports found in '{REPORTS_DIR}/' directory")
        st.error(f"""
        ### No Trading Reports Found
        
        No session reports were found in the `{REPORTS_DIR}/` directory.
        
        **To generate reports:**
        1. Run your trading bot
        2. Use the command: `auto start [options] --s`
        3. Trade and then stop with: `auto stop` or `quit`
        4. Reports will be automatically saved
        
        The report viewer will then display them here!
        """)
        return
    
    # Display session count
    st.sidebar.success(f"Found {len(sessions)} session(s)")
    
    # Session selection
    session_options = []
    for session in sessions:
        profit_loss = session['total_profit_loss']
        emoji = "📈" if profit_loss > 0 else "📉" if profit_loss < 0 else "➖"
        label = f"{emoji} {session['session_id']} (${profit_loss:+.2f})"
        session_options.append(label)
    
    selected_index = st.sidebar.selectbox(
        "Select a session to view:",
        range(len(session_options)),
        format_func=lambda i: session_options[i]
    )
    
    selected_session = sessions[selected_index]
    session_data = selected_session['data']
    
    st.sidebar.divider()
    
    # Session quick info
    st.sidebar.markdown("### Quick Info")
    st.sidebar.markdown(f"**Start:** {session_data.get('start_time', 'N/A')}")
    st.sidebar.markdown(f"**End:** {session_data.get('end_time', 'N/A')}")
    st.sidebar.markdown(f"**Account:** {session_data.get('account_type', 'N/A')}")
    profit_loss = session_data.get('total_profit_loss', 0)
    st.sidebar.markdown(f"**P/L:** {format_currency(profit_loss)}", unsafe_allow_html=True)
    
    st.sidebar.divider()
    
    # Export options
    st.sidebar.markdown("### Export")
    if st.sidebar.button("📥 Download JSON", use_container_width=True):
        with open(selected_session['filepath'], 'r') as f:
            json_str = f.read()
        st.sidebar.download_button(
            label="💾 Save File",
            data=json_str,
            file_name=selected_session['filename'],
            mime='application/json',
            use_container_width=True
        )
    
    # Main content
    display_session_overview(session_data)
    
    display_statistics(session_data)
    
    st.divider()
    
    display_strategy_config(session_data)
    
    st.divider()
    
    display_charts(session_data)
    
    st.divider()
    
    display_trades_table(session_data)
    
    st.divider()
    
    display_cycles(session_data)
    
    st.divider()
    
    display_events(session_data)
    
    # Termination info
    st.divider()
    st.subheader("🏁 Session Termination")
    termination = session_data.get('termination', {})
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Reason", termination.get('reason', 'Unknown'))
    with col2:
        st.metric("Timestamp", termination.get('timestamp', 'N/A'))
    with col3:
        was_planned = termination.get('was_planned', False)
        status = "✅ Planned" if was_planned else "⚠️ Unexpected"
        st.metric("Status", status)


if __name__ == "__main__":
    main()