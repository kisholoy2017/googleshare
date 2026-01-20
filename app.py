import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google.ads.googleads.client import GoogleAdsClient
from datetime import datetime
from dateutil.relativedelta import relativedelta
import yaml
import tempfile
import os
import time

# Page config
st.set_page_config(page_title="Share of Search", page_icon="📊", layout="wide")

st.title("📊 Share of Search Analysis")

# Sidebar - Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Configuration
    st.subheader("1. Google Ads API")
    uploaded_file = st.file_uploader("Upload google-ads.yaml", type=['yaml', 'yml'])
    
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.yaml', mode='wb') as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name
        
        with open(tmp_path, 'r') as f:
            config = yaml.safe_load(f)
        
        customer_id = st.text_input("Customer ID", value=config.get('customer_id', ''))
        
        st.subheader("2. Analysis Settings")
        target_brand = st.text_input("Target Brand", value="LampTwist")
        
        competitor_brands_text = st.text_area(
            "Competitor Brands (one per line)",
            value="MOHD\nLa Redoute\nwest elm\nWayfair",
            height=150
        )
        competitor_brands = [b.strip() for b in competitor_brands_text.split('\n') if b.strip()]
        
        st.subheader("3. Date Range")
        months_back = st.slider("Months of data", 3, 24, 12)
        
        st.subheader("4. Location & Language")
        country = st.selectbox("Country", ["Belgium", "United States", "United Kingdom", "France", "Germany"])
        language = st.selectbox("Language", ["English", "French", "Dutch", "German", "Spanish"])
        
        run_button = st.button("🚀 Run Analysis", type="primary", use_container_width=True)
        
        os.unlink(tmp_path)
    else:
        st.info("Upload your google-ads.yaml file to begin")
        run_button = False
        customer_id = None

# Country and language mappings
COUNTRIES = {
    "Belgium": "2056", "United States": "2840", "United Kingdom": "2826",
    "France": "2250", "Germany": "2276"
}

LANGUAGES = {
    "English": "1000", "French": "1002", "Dutch": "1010",
    "German": "1003", "Spanish": "1003"
}

def get_keyword_volumes(client, customer_id, brand, location_id, language_id, months_back):
    """Get keyword search volumes with monthly breakdown"""
    
    try:
        # Calculate date range
        end_date = datetime.now().replace(day=1) - relativedelta(days=1)
        start_date = end_date - relativedelta(months=months_back - 1)
        
        # Services
        keyword_service = client.get_service("KeywordPlanIdeaService")
        geo_service = client.get_service("GeoTargetConstantService")
        
        # Build request
        request = client.get_type("GenerateKeywordIdeasRequest")
        request.customer_id = customer_id
        request.language = client.get_service("GoogleAdsService").language_constant_path(language_id)
        request.geo_target_constants = [geo_service.geo_target_constant_path(location_id)]
        request.keyword_plan_network = client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH
        request.keyword_seed.keywords.append(brand.lower())
        
        # Historical metrics
        request.historical_metrics_options.year_month_range.start.year = start_date.year
        request.historical_metrics_options.year_month_range.start.month = start_date.month
        request.historical_metrics_options.year_month_range.end.year = end_date.year
        request.historical_metrics_options.year_month_range.end.month = end_date.month
        
        # Get ideas
        response = keyword_service.generate_keyword_ideas(request=request)
        
        # Process results
        monthly_volumes = {}
        total_avg = 0
        keywords = []
        
        for idea in response:
            if brand.lower() in idea.text.lower():
                metrics = idea.keyword_idea_metrics
                total_avg += metrics.avg_monthly_searches or 0
                keywords.append(idea.text)
                
                if metrics.monthly_search_volumes:
                    for mv in metrics.monthly_search_volumes:
                        month_key = f"{mv.year}-{mv.month:02d}"
                        monthly_volumes[month_key] = monthly_volumes.get(month_key, 0) + (mv.monthly_searches or 0)
        
        return {
            'brand': brand,
            'avg_volume': total_avg,
            'monthly_volumes': monthly_volumes,
            'keywords': keywords
        }
        
    except Exception as e:
        st.error(f"Error for {brand}: {str(e)}")
        return {
            'brand': brand,
            'avg_volume': 0,
            'monthly_volumes': {},
            'keywords': []
        }

# Main execution
if run_button and customer_id:
    
    with st.spinner("Loading Google Ads client..."):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.yaml', mode='wb') as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            
            client = GoogleAdsClient.load_from_storage(tmp_path, version="v22")
            os.unlink(tmp_path)
            
        except Exception as e:
            st.error(f"Failed to initialize client: {e}")
            st.stop()
    
    location_id = COUNTRIES[country]
    language_id = LANGUAGES[language]
    
    # Collect data
    all_brands = [target_brand] + competitor_brands
    results = []
    
    progress_bar = st.progress(0)
    status = st.empty()
    
    for i, brand in enumerate(all_brands):
        status.text(f"Analyzing {brand}... ({i+1}/{len(all_brands)})")
        
        data = get_keyword_volumes(
            client, customer_id.replace('-', ''), brand,
            location_id, language_id, months_back
        )
        results.append(data)
        
        progress_bar.progress((i + 1) / len(all_brands))
        
        if i < len(all_brands) - 1:
            time.sleep(2)
    
    status.text("Analysis complete!")
    progress_bar.empty()
    
    # Process results
    if any(r['avg_volume'] > 0 for r in results):
        
        # Average volumes
        df_avg = pd.DataFrame([{
            'brand': r['brand'],
            'avg_volume': r['avg_volume'],
            'is_target': r['brand'] == target_brand
        } for r in results])
        
        total_volume = df_avg['avg_volume'].sum()
        df_avg['share_of_search'] = (df_avg['avg_volume'] / total_volume * 100).round(2)
        df_avg = df_avg.sort_values('avg_volume', ascending=False).reset_index(drop=True)
        
        # Monthly trends
        monthly_data = []
        for r in results:
            for month, volume in r['monthly_volumes'].items():
                monthly_data.append({
                    'brand': r['brand'],
                    'month': month,
                    'volume': volume
                })
        
        df_monthly = pd.DataFrame(monthly_data)
        
        if not df_monthly.empty:
            monthly_totals = df_monthly.groupby('month')['volume'].sum().reset_index()
            monthly_totals.columns = ['month', 'total']
            
            df_monthly = df_monthly.merge(monthly_totals, on='month')
            df_monthly['share_of_search'] = (df_monthly['volume'] / df_monthly['total'] * 100).round(2)
        
        # Display results
        st.success("✅ Analysis complete!")
        
        # Key metrics
        st.header("📊 Key Metrics")
        target_row = df_avg[df_avg['is_target']].iloc[0]
        leader_row = df_avg.iloc[0]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Target Brand SoS", f"{target_row['share_of_search']:.2f}%")
        
        with col2:
            st.metric("Search Volume", f"{target_row['avg_volume']:,}")
        
        with col3:
            rank = (df_avg['avg_volume'] > target_row['avg_volume']).sum() + 1
            st.metric("Market Rank", f"#{rank}")
        
        with col4:
            st.metric("Market Leader", leader_row['brand'])
        
        # Tabs
        tab1, tab2, tab3 = st.tabs(["📈 Trends", "📊 Summary", "📋 Data"])
        
        with tab1:
            if not df_monthly.empty:
                st.subheader("Share of Search Over Time")
                
                fig = go.Figure()
                
                for brand in df_monthly['brand'].unique():
                    brand_data = df_monthly[df_monthly['brand'] == brand].sort_values('month')
                    
                    fig.add_trace(go.Scatter(
                        x=brand_data['month'],
                        y=brand_data['share_of_search'],
                        mode='lines+markers',
                        name=brand,
                        line=dict(width=3 if brand == target_brand else 2)
                    ))
                
                fig.update_layout(
                    xaxis_title="Month",
                    yaxis_title="Share of Search (%)",
                    hovermode='x unified',
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No monthly data available")
        
        with tab2:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Search Volume by Brand")
                fig = px.bar(
                    df_avg, x='avg_volume', y='brand',
                    orientation='h',
                    color='is_target',
                    color_discrete_map={True: '#FF6B6B', False: '#4ECDC4'}
                )
                fig.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("Market Share")
                fig = px.pie(
                    df_avg, values='avg_volume', names='brand',
                    hole=0.3
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            st.subheader("Brand Rankings")
            display_df = df_avg[['brand', 'avg_volume', 'share_of_search']].copy()
            display_df.columns = ['Brand', 'Avg Monthly Volume', 'Share of Search (%)']
            st.dataframe(display_df, use_container_width=True)
            
            # Download
            csv = df_avg.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Download Summary CSV",
                csv,
                f"sos_summary_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv"
            )
            
            if not df_monthly.empty:
                csv_trends = df_monthly.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Download Trends CSV",
                    csv_trends,
                    f"sos_trends_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv"
                )
    
    else:
        st.error("❌ No data collected. Check your settings and try again.")

elif not uploaded_file:
    st.info("👈 Upload your google-ads.yaml file in the sidebar to begin")

else:
    st.info("👈 Configure your analysis in the sidebar and click 'Run Analysis'")
