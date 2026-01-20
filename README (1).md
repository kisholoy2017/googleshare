# Share of Search Analysis App

Clean, from-scratch implementation of Share of Search analysis using Google Ads API.

## Features

- **Monthly Evolution:** Track search volumes month-by-month over your chosen date range
- **Share of Search:** Calculate competitive market share based on search volumes
- **Interactive Visualizations:** Trends charts, bar charts, and pie charts
- **Multi-brand Comparison:** Compare your brand against unlimited competitors
- **CSV Export:** Download all data for further analysis

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Prepare Google Ads API Credentials

You need a `google-ads.yaml` file with your API credentials:

```yaml
developer_token: YOUR_DEV_TOKEN
client_id: YOUR_CLIENT_ID
client_secret: YOUR_CLIENT_SECRET
refresh_token: YOUR_REFRESH_TOKEN
customer_id: YOUR_CUSTOMER_ID
login_customer_id: YOUR_MCC_ID  # If using manager account
use_proto_plus: True
```

### 3. Run the App

```bash
streamlit run app.py
```

## Usage

1. **Upload Credentials:** Upload your `google-ads.yaml` file in the sidebar
2. **Configure Analysis:**
   - Enter your Customer ID
   - Set target brand name
   - Add competitor brands (one per line)
   - Choose date range (months of historical data)
   - Select country and language
3. **Run Analysis:** Click "Run Analysis" button
4. **View Results:**
   - **Trends tab:** See month-by-month evolution
   - **Summary tab:** View overall market share
   - **Data tab:** Download CSV exports

## How It Works

The app:
1. Connects to Google Ads API using your credentials
2. Fetches keyword search volumes for each brand
3. Requests monthly historical data for the specified time period
4. Calculates Share of Search (brand volume / total category volume)
5. Generates interactive visualizations
6. Provides CSV downloads for further analysis

## Date Range

The app automatically calculates the date range:
- **End date:** Last complete month (not current month)
- **Start date:** X months before end date (based on your selection)
- This avoids "Invalid date" errors from requesting incomplete data

## Troubleshooting

### "Invalid date" errors

If you still get date errors:
- The app uses the last complete month as end date
- Decrease "Months of data" slider to use a shorter range
- Check that your API credentials have proper permissions

### "Permission denied" errors

- Ensure `login_customer_id` is set in your YAML (if using MCC)
- Verify your OAuth user has access to the customer account
- Check that developer token is approved (not in test mode)

### No data collected

- Verify brand names are spelled correctly
- Try broader brand terms (e.g., "Nike" instead of "Nike Air Max")
- Check that country/language settings match your target market

## Support

For Google Ads API issues:
- [API Documentation](https://developers.google.com/google-ads/api)
- [Authentication Guide](https://developers.google.com/google-ads/api/docs/oauth/overview)
