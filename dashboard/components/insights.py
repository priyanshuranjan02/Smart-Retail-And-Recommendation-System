"""
Smart Retail Analytics Dashboard — Business Intelligence & Domain Insights
Provides contextual callouts, educational disclaimers, and strategic segment playbooks.
"""

import streamlit as st


def render_kpi_definitions_callout():
    """Render informative note on KPI calculations and data boundaries."""
    with st.expander("ℹ️ KPI Definitions, Math & Data Boundaries (Click to expand)", expanded=False):
        st.markdown("""
        - **Gross Revenue (£):** $\\sum (\\text{Quantity} \\times \\text{UnitPrice})$. Note: The UCI Online Retail dataset contains top-line transaction prices without Cost of Goods Sold (COGS). Therefore, this metric reflects **Gross Revenue/Sales**, not Net Profit.
        - **Total Orders:** Count of unique `InvoiceNo` occurrences after excluding cancellations (`C` prefixes) and negative adjustments.
        - **Average Order Value (AOV):** $\\frac{\\text{Gross Revenue}}{\\text{Total Orders}}$. Measures the average spend per checkout cart.
        - **Average Line Item Value:** $\\frac{\\text{Gross Revenue}}{\\text{Total Fact Rows}}$. Measures the average value of individual SKU line items.
        - **Data Integrity:** All cancelled orders and zero/negative quantity or price adjustments are removed during ETL to preserve accounting truth.
        """)


def render_mba_educational_callout():
    """Render educational card explaining Support, Confidence, and Lift with correlation caveat."""
    with st.expander("📖 Market Basket Analysis Methodology & Statistical Definitions", expanded=False):
        st.markdown("""
        **Association Rule Mining (Apriori Algorithm):**
        - **Support ($P(A \\cap B)$):** Proportion of all transactions containing both itemset $A$ and itemset $B$. Measures how widespread a basket pattern is across the customer base.
        - **Confidence ($P(B|A) = \\frac{P(A \\cap B)}{P(A)}$):** Proportion of transactions containing antecedent $A$ that also contain consequent $B$. Measures predictability.
        - **Lift ($\\frac{P(B|A)}{P(B)}$):** The ratio of observed co-occurrence to expected co-occurrence if items were purchased independently:
          - $\\text{Lift} = 1$: Items occur together purely by random chance.
          - $\\text{Lift} > 1$: Positive association. Items are complementary and co-purchased significantly more frequently than chance.
          - $\\text{Lift} < 1$: Negative association (substitutes).
        
        > **⚠️ Important Causal Caveat:** High lift indicates strong **statistical co-purchase affinity**, not direct proof that buying $A$ caused the purchase of $B$. Recommendation campaigns should treat these as cross-sell test hypotheses.
        """)


def render_segment_playbook():
    """Display strategic marketing action plans for each customer tier."""
    col1, col2 = st.columns(2)
    with col1:
        st.info("""
        ### 🏆 Champions (High-Value / Wholesalers)
        - **Profile:** Ultra-high spend (Mean £127k), weekly order cadence (82+ orders), recent (7d).
        - **Business Objective:** Retain, Protect & Partner.
        - **Strategy:** Assign dedicated VIP account manager, offer negotiated tiered volume discounts, early access to inventory.
        - **Monitoring KPI:** B2B retention rate, Order frequency stability.
        """)
        st.success("""
        ### 🥈 Loyal Customers
        - **Profile:** Consistent repeat buyers (Mean 22 orders, £12.7k spend), recent purchases (15d).
        - **Business Objective:** Cultivate Lifetime Value & Cross-sell.
        - **Strategy:** Tiered loyalty club rewards, personalized bundle recommendations, seasonal gifting previews.
        - **Monitoring KPI:** Average Order Value (AOV), Annual retention.
        """)
    with col2:
        st.warning("""
        ### 🛒 Regular Customers
        - **Profile:** Active mainstream shoppers (Mean 3.7 orders, £1.35k spend), moderate recency (44d).
        - **Business Objective:** Nurture, Activate & Upsell.
        - **Strategy:** Automated post-purchase trigger emails, category discovery discounts, free-shipping basket thresholds.
        - **Monitoring KPI:** Second-order conversion rate, Purchase frequency.
        """)
        st.error("""
        ### ⚠️ At-Risk / Lapsed Customers
        - **Profile:** Dormant accounts (>200 days since last order), low lifetime frequency (1-2 orders).
        - **Business Objective:** Win-back or Efficiently Deprioritize.
        - **Strategy:** "We miss you" re-engagement email with limited-time reactivation coupon; exit feedback survey.
        - **Monitoring KPI:** Reactivation rate, Re-acquisition cost efficiency.
        """)


def render_footer():
    """Render consistent, clean application footer."""
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: #78909C; font-size: 0.85rem; padding: 10px 0;">
            <b>Smart Retail Analytics & Recommendation Warehouse</b> &bull; 
            Powered by SQLite Star Schema, Scikit-Learn K-Means, mlxtend Apriori & Streamlit &bull; 
            Dataset: <a href="https://archive.ics.uci.edu/ml/datasets/Online+Retail" target="_blank" style="color: #1E88E5;">UCI Online Retail (541K Records)</a>
        </div>
        """,
        unsafe_allow_html=True
    )
