# 📊 Digital Gender Divide in Morocco: Facebook, Internet, and Mobile Usage

This repository contains the data processing pipeline, spatial harmonization scripts, and visualization notebooks used to produce the *Female-to-Male Digital Usage Indices* for Morocco.  
The analysis integrates **Meta (Facebook)** audience data, **official population statistics**, and **Sustainable Development Goal (SDG)** indicators to quantify and map gender differences in digital access at the regional level.

---

## 🧭 Repository Structure

├── APP1.ipynb # Main notebook: data acquisition, harmonization, and visualization
├── data_raw/ # Raw input data (Facebook API outputs, HDX shapefiles, SDG tables)
├── data_processed/ # Harmonized data (merged and cleaned DataFrames)
├── figures/ # Choropleth maps and analytical visualizations
├── environment.yml # Conda environment (Python 3.12, geopandas, matplotlib, etc.)
└── README.md # Project documentation 

---

## 🧩 1. Facebook Data Acquisition, Processing, and Spatial Integration

### 1.1 Setting up Access to Facebook Data

To retrieve Meta data:

1. Create a **Meta for Developers** account and register an application on the [Meta Developers Dashboard](https://developers.facebook.com/).
2. Obtain:
   - **App Account ID**
   - **Access Token**
3. Store all credentials securely in a `.env` file:

META_ACCESS_TOKEN=
META_AD_ACCOUNT_ID=


---

## ⚙️ Requirements

### Python Version
- **Python 3.12.7**

### Required Libraries
The analysis requires the following Python packages:

```bash
pandas
geopandas
matplotlib
requests
rasterstats
python-dotenv
```

This work integrates data from:

Meta for Developers – Graph API

Humanitarian Data Exchange (HDX)

Haut-Commissariat au Plan (HCP)

World Bank Open Data

ITU SDG DataHub


## 🧩 1. Facebook (Meta) Data Acquisition, Processing, and Spatial Integration (detailed instructions)

### 1.1 Creating a Meta for Developers Account

1. Visit the official Meta Developers portal: [https://developers.facebook.com/](https://developers.facebook.com/).
2. Log in using your personal Facebook account.
3. Go to **My Apps → Create App**.
4. Choose **Business** or **Other** as the app type (either works for data access).
5. Fill in the required details (app name, email, purpose) and click **Create App**.
6. Once the app is created, you will see:
   - **App ID**
   - **App Secret**
   - **App Dashboard** where you can manage tokens and permissions.

These credentials are required to authenticate access to the **Meta Graph API**.

---

### 1.2 Generating an Access Token

There are two main ways to generate your Access Token.

#### **Option A – Using the Graph API Explorer**

1. Open the **Graph API Explorer** tool: [https://developers.facebook.com/tools/explorer](https://developers.facebook.com/tools/explorer)
2. In the top-right menu, select your app under **Meta App → Select App**.
3. Click **Generate Access Token**.
4. When prompted, select the following permissions:
   - `ads_read`
   - `ads_management`
   - `pages_read_engagement` (optional if you need page-level data)
5. Copy the generated token.  
   It looks like a long string of letters and numbers, for example:
EAAJZC2XXXXXXXXXXXXXXX

> ⚠️ **Note:** Tokens from the Graph API Explorer expire after a few hours.  
> For permanent access, create a **System User Token** under *Business Settings → System Users* and assign the user an ad account with `ads_read` permission.

#### **Option B – Using Business Settings**

1. Go to [https://business.facebook.com/settings/system-users](https://business.facebook.com/settings/system-users)
2. Create a **System User** (Admin Role).
3. Generate a **Permanent Access Token** for your app.
4. Assign permissions (`ads_read`, `ads_management`) to the same ad account you will query.

---

### 1.3 Obtaining the Ad Account ID (`act_XXXXXXXXXXXX`)

The Ad Account ID identifies the data source within Meta’s ecosystem.

#### **Option A – From Facebook Ads Manager**

1. Open [https://business.facebook.com/adsmanager](https://business.facebook.com/adsmanager)
2. In the top-left dropdown, choose the correct **Ad Account**.
3. Look at the browser URL; it should look like:
https://business.facebook.com/adsmanager/manage/accounts?act=xxxxxxxxx


4. The number after `act=` is your **Ad Account ID**:  
act_xxxxxxxxxxxxxxx



#### **Option B – From the Graph API Explorer**

1. Open the Graph API Explorer again.
2. In the request bar, type:
GET me/adaccounts


3. Click **Submit**.
4. The JSON response should look like:
```json
{
  "data": [
    {
      "id": "act_xxxxxxxxxxxxxxxxx",
      "account_status": 1,
      "name": "My Ad Account"
    }
  ]
}
Copy the value under "id" — that is your META_AD_ACCOUNT_ID.

1.4 Storing Credentials Securely
Create a file named .env in the root of your repository with the following structure:


META_APP_ID=xxxxxxxxxxxxxxxx
META_APP_SECRET=xxxxxxxxxxxxxxxx
META_ACCESS_TOKEN=EAAJZC2XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
META_AD_ACCOUNT_ID=act_xxxxxxxxxxxxxxxx
Load the credentials securely in your Python code:


from dotenv import load_dotenv
import os

load_dotenv()

token = os.getenv("META_ACCESS_TOKEN")
account_id = os.getenv("META_AD_ACCOUNT_ID")