import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import streamlit as st



# ----------------------------
# PAGE STATE
# ----------------------------
if "page" not in st.session_state:
    st.session_state.page = "home"



def home_page():
    st.title("📌 CBZ Credit Risk Analytics Suite")

    st.markdown("### Select Functionality")

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        if st.button("📊 Credit Migration Dashboard", use_container_width=True):
            st.session_state.page = "migration"

    with col2:
        if st.button("⚡ Automated Credit Transition", use_container_width=True):
            st.session_state.page = "scoring"
    with col3:
     
        if st.button("⚡ Maturity Profiling", use_container_width=True):
            st.warning("🚧 Under Development.")
    with col4:
        if st.button("📉 Credit Risk Appetite", use_container_width=True):
            st.session_state.page = "scoring"
    with col5:
        if st.button("⚡ Scenario Analytics", use_container_width=True):
            st.warning("🚧 Coming Soon.")
    with col6:
        if st.button("📊 Automated All Loans ODs Consolidation", use_container_width=True):
            st.warning("🚧 Coming Soon.")


def back_button():
    if st.button("⬅ Back to Home"):
        st.session_state.page = "home"


def credit_migration_dashboard():
    back_button()
    
    st.title("📊 Credit Migration Dashboard")
    st.set_page_config(page_title="Credit Migration Dashboard", layout="wide")
    st.title("📊 Credit Migration Dashboard")

    # ----------------------------
    # FILE UPLOAD
    # ----------------------------
    st.sidebar.header("Upload Files")

    prev_file = st.sidebar.file_uploader("Previous Month Report", type=["xlsx"])
    curr_file = st.sidebar.file_uploader("Current Month Report", type=["xlsx"])

    if prev_file and curr_file:

        # ----------------------------
        # LOAD DATA
        # ----------------------------
        df_prev = pd.read_excel(prev_file, engine='openpyxl')
        df_curr = pd.read_excel(curr_file, engine='openpyxl')

        # RUN BUTTON
        # ----------------------------
        run_analysis = st.sidebar.button(
            "▶ Run Migration Analysis",
            use_container_width=True
        )

    if prev_file and curr_file and run_analysis:

        # ----------------------------
        # CLEAN COLUMN NAMES
        # ----------------------------
        df_prev.columns = df_prev.columns.str.strip().str.upper()
        df_curr.columns = df_curr.columns.str.strip().str.upper()

        # ----------------------------
        # SELECT COLUMNS
        # ----------------------------
        cols = [
            'CLIENT REF NO',
            'CLIENT NAME',
            'INTERNAL RATING',
            'STAGE',
            'ALL USD EXPO',
            'ALL USD ECL',
            'DASHBOARD LENDING UNIT',
            'SECTOR'
        ]

        df_prev = df_prev[cols]
        df_curr = df_curr[cols]

        # ----------------------------
        # CLEAN RATINGS (CRITICAL)
        # ----------------------------
        df_prev['INTERNAL RATING'] = df_prev['INTERNAL RATING'].astype(str).str.strip().str.upper()
        df_curr['INTERNAL RATING'] = df_curr['INTERNAL RATING'].astype(str).str.strip().str.upper()

        # ----------------------------
        # ADD SUFFIXES
        # ----------------------------
        df_prev = df_prev.add_suffix('_PREV')
        df_curr = df_curr.add_suffix('_CURR')

        # ----------------------------
        # MERGE
        # ----------------------------
        df = pd.merge(
            df_prev,
            df_curr,
            left_on='CLIENT REF NO_PREV',
            right_on='CLIENT REF NO_CURR',
            how='outer',
            sort=False
        )

        # ----------------------------
        # CLEAN IDENTIFIERS
        # ----------------------------
        df['CLIENT REF NO'] = df['CLIENT REF NO_PREV'].combine_first(df['CLIENT REF NO_CURR'])
        df['CLIENT NAME'] = df['CLIENT NAME_CURR'].combine_first(df['CLIENT NAME_PREV'])

        # ----------------------------
        # RATING SCALE
        # ---------------------------------------------------------------------------------------------------------
        
        # RATING SCALE
        # ----------------------------
        rating_rank = {
            'A+': 1,
            'A': 2,
            'A-': 3,
            'AB+': 4,
            'AB': 5,
            'AB-': 6,
            'B+': 7,
            'B': 8,
            'B-': 9,
            'BC+': 10,
            'BC': 11,
            'BC-': 12,
            'C+': 13,
            'C': 14,
            'C-': 15,
            'CD+': 16,
            'CD': 17,
            'CD-': 18,
            'D+': 19,
            'D': 20,
            'D-': 21
        }

        # ----------------------------
        # CLEAN RATINGS
        # ----------------------------
        df['INTERNAL RATING_PREV'] = (
            df['INTERNAL RATING_PREV']
            .astype(str)
            .str.strip()
            .str.upper()
            .str.replace(r'\s+', '', regex=True)
        )

        df['INTERNAL RATING_CURR'] = (
            df['INTERNAL RATING_CURR']
            .astype(str)
            .str.strip()
            .str.upper()
            .str.replace(r'\s+', '', regex=True)
        )

        # ----------------------------
        # MAP TO NUMERIC RANKS
        # ----------------------------
        df['RATING_PREV_NUM'] = df['INTERNAL RATING_PREV'].map(rating_rank)
        df['RATING_CURR_NUM'] = df['INTERNAL RATING_CURR'].map(rating_rank)

        # ----------------------------
        # CALCULATE MOVEMENT
        # ----------------------------
        df['RATING_DIFFERENCE'] = (
            df['RATING_CURR_NUM']
            - df['RATING_PREV_NUM']
        )

        # ----------------------------
        # RATING MOVEMENT TEXT
        # ----------------------------
        df['Rating Movement'] = (
            df['INTERNAL RATING_PREV'].fillna('NEW')
            + ' → ' +
            df['INTERNAL RATING_CURR'].fillna('EXIT')
        )

        # ----------------------------
        # NUMBER OF NOTCHES MOVED
        # ----------------------------
        df['NOTCH_MOVEMENT'] = abs(df['RATING_DIFFERENCE'])

        # ----------------------------
        # CREDIT MIGRATION LOGIC
        # ----------------------------
        df['Migration'] = 'UNCHANGED'

        # NEW CLIENTS
        df.loc[
            df['CLIENT REF NO_PREV'].isna(),
            'Migration'
        ] = 'NEW'

        # PAID OFF CLIENTS
        df.loc[
            df['CLIENT REF NO_CURR'].isna(),
            'Migration'
        ] = 'PAID_OFF'

        # DETERIORATED
        df.loc[
            (df['CLIENT REF NO_PREV'].notna()) &
            (df['CLIENT REF NO_CURR'].notna()) &
            (df['RATING_DIFFERENCE'] > 0),
            'Migration'
        ] = 'DETERIORATED'

        # IMPROVED
        df.loc[
            (df['CLIENT REF NO_PREV'].notna()) &
            (df['CLIENT REF NO_CURR'].notna()) &
            (df['RATING_DIFFERENCE'] < 0),
            'Migration'
        ] = 'IMPROVED'

        # UNCHANGED
        df.loc[
            (df['CLIENT REF NO_PREV'].notna()) &
            (df['CLIENT REF NO_CURR'].notna()) &
            (df['RATING_DIFFERENCE'] == 0),
            'Migration'
        ] = 'UNCHANGED'

        #------------------------------------------------------------------------------------------------------------

        # ----------------------------
        # KPI SECTION
        # ----------------------------
        total_exposure = df['ALL USD EXPO_CURR'].sum()
        det_exposure = df.loc[df['Migration']=='DETERIORATED', 'ALL USD EXPO_CURR'].sum()
        imp_exposure = df.loc[df['Migration']=='IMPROVED', 'ALL USD EXPO_CURR'].sum()
        new_exposure = df.loc[df['Migration']=='NEW', 'ALL USD EXPO_CURR'].sum()

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Exposure", f"{total_exposure:,.0f}")
        col2.metric("Deteriorated", f"{det_exposure:,.0f}")
        col3.metric("Improved", f"{imp_exposure:,.0f}")
        col4.metric("New Facilities", f"{new_exposure:,.0f}")
            # PORTFOLIO SUMMARY TABLE
        # ----------------------------

        st.subheader("📊 Credit Migration Portfolio")
        
        summary = pd.DataFrame({
        'Category': [
            'Deteriorated',
            'Upgraded/Improved',
            'Unchanged/Static',
            'New On-board Facilities',
            'Paid Off'
        ],
        'Prev Month': [
            df.loc[df['Migration'] == 'DETERIORATED', 'ALL USD EXPO_PREV'].sum(),
            df.loc[df['Migration'] == 'IMPROVED', 'ALL USD EXPO_PREV'].sum(),
            df.loc[df['Migration'] == 'UNCHANGED', 'ALL USD EXPO_PREV'].sum(),
            df.loc[df['Migration'] == 'NEW', 'ALL USD EXPO_CURR'].sum(),
            df.loc[df['Migration'] == 'PAID_OFF', 'ALL USD EXPO_PREV'].sum()
        ],
        'Current Month': [
            df.loc[df['Migration'] == 'DETERIORATED', 'ALL USD EXPO_CURR'].sum(),
            df.loc[df['Migration'] == 'IMPROVED', 'ALL USD EXPO_CURR'].sum(),
            df.loc[df['Migration'] == 'UNCHANGED', 'ALL USD EXPO_CURR'].sum(),
            df.loc[df['Migration'] == 'NEW', 'ALL USD EXPO_CURR'].sum(),
            df.loc[df['Migration'] == 'PAID_OFF', 'ALL USD EXPO_PREV'].sum()
        ]
        })
            # =============================
        # TOTALS
        # =============================

        #total_prev = summary['Prev Month'].sum()
        #total_curr = summary['Current Month'].sum()
        
        total_prev = summary.loc[
            summary['Category'] != 'Paid Off',
            'Prev Month'
        ].sum()

        total_curr = summary.loc[
            summary['Category'] != 'Paid Off',
            'Current Month'
        ].sum()


        # Add % Concentration (based on Current Month)
        summary['% Concentration'] = (summary['Current Month'] / total_curr) * 100

        # =============================
        # ADD GRAND TOTAL ROW
        # =============================

        total_row = pd.DataFrame({
        'Category': ['Reported Advances Value'],
        'Prev Month': [total_prev],
        'Current Month': [total_curr],
        '% Concentration': [100]
        })

        summary = pd.concat([summary, total_row], ignore_index=True)
        summary = summary.set_index('Category')
        
            
        def highlight_total(row):
            if row.name == 'Reported Advances Value':
                return ['background-color: #002060; color: white; font-weight: bold'] * len(row)
            return [''] * len(row)
        
        styled = (
        summary.style
        .format({
            'Prev Month': '{:,.0f}',
            'Current Month': '{:,.0f}',
            '% Concentration': '{:.2f}%'
        })
        .background_gradient(subset=['Prev Month'], cmap='Blues')
        .background_gradient(subset=['Current Month'], cmap='Greens')
        .background_gradient(subset=['% Concentration'], cmap='Oranges')
        .apply(highlight_total, axis=1)
        )
        st.dataframe(styled, use_container_width=True)
        
        # DETERIORATION BY SECTOR
        # ----------------------------
        st.subheader("🏭 Deterioration by Sector")

        # Aggregate data
        by_sector = (
        df[df['Migration'] == 'DETERIORATED']
        .groupby('SECTOR_CURR')['ALL USD EXPO_CURR']
        .sum()
        .reset_index()
        )

        # Create Pie Chart

        fig = px.pie(
        by_sector,
        names='SECTOR_CURR',
        values='ALL USD EXPO_CURR',
        title='Deteriorated Accounts by Sector',
        color_discrete_sequence=px.colors.qualitative.Bold  # vibrant colors
        )


        # Show % and labels clearly
        fig.update_traces(
        textinfo='percent+label',   # show both label & %
        pull=[0.05]*len(by_sector),  # slight separation for all slices
        textfont_size=14
        )

        # Improve layout
        fig.update_layout(
        title_font_size=18,
        legend_title="Sector"
        )

        st.plotly_chart(fig, use_container_width=True)
            # DETERIORATION BY UNIT
        # ----------------------------
        st.subheader("🏢 Deterioration by Lending Unit")
        
        
        # Aggregate data
        by_unit = (
        df[df['Migration'] == 'DETERIORATED']
        .groupby('DASHBOARD LENDING UNIT_CURR')
        .agg({
            'ALL USD EXPO_CURR': 'sum',
            'ALL USD ECL_CURR': 'sum'
        })
        .sort_values(by='ALL USD EXPO_CURR', ascending=False)
        )

        # Rename columns for display
        by_unit.columns = ['USD Exposure', 'USD ECL']

        # Calculate percentages
        by_unit['% of Total Exposure'] = (by_unit['USD Exposure'] / by_unit['USD Exposure'].sum()) * 100

        # Add Grand Total row
        total_row = pd.DataFrame({
        'USD Exposure': [by_unit['USD Exposure'].sum()],
        'USD ECL': [by_unit['USD ECL'].sum()],
        '% of Total Exposure': [100]
        }, index=['Grand Total'])

        by_unit = pd.concat([by_unit, total_row])

        # Format numbers
        styled_table = (
        by_unit.style
        .format({
            'USD Exposure': '{:,.0f}',
            'USD ECL': '{:,.0f}',
            '% of Total Exposure': '{:.1f}%'
        })
        .background_gradient(subset=['USD Exposure'], cmap='Blues')
        .background_gradient(subset=['USD ECL'], cmap='Oranges')
        .background_gradient(subset=['% of Total Exposure'], cmap='Greens')
        .set_properties(**{
            'font-weight': 'bold'
        })
        )

        st.dataframe(styled_table, use_container_width=True)
        # ----------------------------
        # TOP 10 DETERIORATIONS
        # ----------------------------
        st.subheader("🔟 Top 10 Deteriorating Accounts")

        df['Rating Movement'] = (
            df['INTERNAL RATING_PREV'].fillna('NEW') +
            " → " +
            df['INTERNAL RATING_CURR'].fillna('EXIT')
        )

        top10 = df[df['Migration']=='DETERIORATED'] \
            .sort_values(by='ALL USD EXPO_CURR', ascending=False).head(10)

        st.dataframe(top10[[
            'CLIENT REF NO',
            'CLIENT NAME',
            'Rating Movement',
            'ALL USD EXPO_CURR',
            'ALL USD ECL_CURR'
        ]])
            # FULL DATA
        # ----------------------------
        st.subheader("🔍 Full Migration Data")
        st.dataframe(df)


        # ----------------------------
        # ✅ DEBUG (VERY IMPORTANT)
        # ----------------------------
        st.subheader("🔍 Debug Rating Mapping")

        st.write(
            df[[
                'CLIENT REF NO',
                'CLIENT NAME',
                'INTERNAL RATING_PREV',
                'INTERNAL RATING_CURR',
                'RATING_PREV_NUM',
                'RATING_CURR_NUM',
                'RATING_DIFFERENCE',
                'NOTCH_MOVEMENT',
                'Migration'
            ]].head(20)
        )
        
    else:
        st.info("Please upload both Previous and Current month reports.")

        

def back_button():
    if st.button("⬅ Back to Home"):
        st.session_state.page = "home"

#------------------------------------------------------------------------------------------------------------------------

def automated_credit_scoring():
    back_button()

    st.title("⚡ Automated Credit Transition")

    uploaded_file = st.file_uploader("Upload Input File", type=["xlsx"])

    if uploaded_file:

        # Save uploaded file temporarily
        temp_input = "input file.xlsx"
        with open(temp_input, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # ----------------------------
        # ✅ EXECUTE YOUR CODE AS-IS
        # ----------------------------
        import pandas as pd

        # =============================
        # 1. LOAD INPUT FILE ONLY
        # =============================
        input_file = "input file.xlsx"
        df = pd.read_excel(input_file, engine='openpyxl')


        # =============================
        # 2. DEFINE DPD BANDS
        # =============================
        bands = [0,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100]

        def dpd_to_band(dpd):
            if pd.isna(dpd):
                return None
            for b in bands:
                if dpd <= b:
                    return b
            return 100


        # =============================
        # 3. EMBED TRANSITION MATRIX
        # =============================
        matrix = {
            0:{0:"A+",5:"A",10:"B",15:"B",20:"B",25:"B",30:"B",35:"B",40:"B",45:"BC+",50:"BC",55:"BC-",60:"C+",65:"C",70:"C-",75:"CD+",80:"CD",85:"CD-",90:"D+",95:"D",100:"D-"},
            5:{0:"A",5:"A",10:"A-",15:"AB+",20:"AB",25:"AB-",30:"B+",35:"B",40:"B-",45:"BC+",50:"BC",55:"BC-",60:"C+",65:"C",70:"C-",75:"CD+",80:"CD",85:"CD-",90:"D+",95:"D",100:"D-"},
            10:{0:"A-",5:"A-",10:"A-",15:"AB+",20:"AB",25:"AB-",30:"B+",35:"B",40:"B-",45:"BC+",50:"BC",55:"BC-",60:"C+",65:"C",70:"C-",75:"CD+",80:"CD",85:"CD-",90:"D+",95:"D",100:"D-"},
            15:{0:"AB+",5:"AB+",10:"AB+",15:"AB+",20:"AB",25:"AB-",30:"B+",35:"B",40:"B-",45:"BC+",50:"BC",55:"BC-",60:"C+",65:"C",70:"C-",75:"CD+",80:"CD",85:"CD-",90:"D+",95:"D",100:"D-"},
            20:{0:"AB",5:"AB",10:"AB",15:"AB",20:"AB",25:"AB-",30:"B+",35:"B",40:"B-",45:"BC+",50:"BC",55:"BC-",60:"C+",65:"C",70:"C-",75:"CD+",80:"CD",85:"CD-",90:"D+",95:"D",100:"D-"},
            25:{0:"AB-",5:"AB-",10:"AB-",15:"AB-",20:"AB-",25:"AB-",30:"B+",35:"B",40:"B-",45:"BC+",50:"BC",55:"BC-",60:"C+",65:"C",70:"C-",75:"CD+",80:"CD",85:"CD-",90:"D+",95:"D",100:"D-"},
            30:{0:"B+",5:"B+",10:"B+",15:"B+",20:"B+",25:"B+",30:"B+",35:"B",40:"B-",45:"BC+",50:"BC",55:"BC-",60:"C+",65:"C",70:"C-",75:"CD+",80:"CD",85:"CD-",90:"D+",95:"D",100:"D-"},
            35:{0:"B",5:"B",10:"B",15:"B",20:"B",25:"B",30:"B",35:"B",40:"B-",45:"BC+",50:"BC",55:"BC-",60:"C+",65:"C",70:"C-",75:"CD+",80:"CD",85:"CD-",90:"D+",95:"D",100:"D-"},
            40:{0:"B-",5:"B-",10:"B-",15:"B-",20:"B-",25:"B-",30:"B-",35:"B-",40:"B-",45:"BC+",50:"BC",55:"BC-",60:"C+",65:"C",70:"C-",75:"CD+",80:"CD",85:"CD-",90:"D+",95:"D",100:"D-"},
            45:{0:"BC+",5:"BC+",10:"BC+",15:"BC+",20:"BC+",25:"BC+",30:"BC+",35:"BC+",40:"BC+",45:"BC+",50:"BC",55:"BC-",60:"C+",65:"C",70:"C-",75:"CD+",80:"CD",85:"CD-",90:"D+",95:"D",100:"D-"},
            50:{0:"BC",5:"BC",10:"BC",15:"BC",20:"BC",25:"BC",30:"BC",35:"BC",40:"BC",45:"BC",50:"BC",55:"BC-",60:"C+",65:"C",70:"C-",75:"CD+",80:"CD",85:"CD-",90:"D+",95:"D",100:"D-"},
            55:{0:"BC-",5:"BC-",10:"BC-",15:"BC-",20:"BC-",25:"BC-",30:"BC-",35:"BC-",40:"BC-",45:"BC-",50:"BC-",55:"BC-",60:"C+",65:"C",70:"C-",75:"CD+",80:"CD",85:"CD-",90:"D+",95:"D",100:"D-"},
            60:{0:"C+",5:"C+",10:"C+",15:"C+",20:"C+",25:"C+",30:"C+",35:"C+",40:"C+",45:"C+",50:"C+",55:"C+",60:"C+",65:"C",70:"C-",75:"CD+",80:"CD",85:"CD-",90:"D+",95:"D",100:"D-"},
            65:{0:"C",5:"C",10:"C",15:"C",20:"C",25:"C",30:"C",35:"C",40:"C",45:"C",50:"C",55:"C",60:"C",65:"C",70:"C-",75:"CD+",80:"CD",85:"CD-",90:"D+",95:"D",100:"D-"},
            70:{0:"C-",5:"C-",10:"C-",15:"C-",20:"C-",25:"C-",30:"C-",35:"C-",40:"C-",45:"C-",50:"C-",55:"C-",60:"C-",65:"C-",70:"C-",75:"CD+",80:"CD",85:"CD-",90:"D+",95:"D",100:"D-"},
            75:{0:"CD+",5:"CD+",10:"CD+",15:"CD+",20:"CD+",25:"CD+",30:"CD+",35:"CD+",40:"CD+",45:"CD+",50:"CD+",55:"CD+",60:"CD+",65:"CD+",70:"CD+",75:"CD+",80:"CD",85:"CD-",90:"D+",95:"D",100:"D-"},
            80:{0:"CD",5:"CD",10:"CD",15:"CD",20:"CD",25:"CD",30:"CD",35:"CD",40:"CD",45:"CD",50:"CD",55:"CD",60:"CD",65:"CD",70:"CD",75:"CD",80:"CD",85:"CD-",90:"D+",95:"D",100:"D-"},
            85:{0:"CD-",5:"CD-",10:"CD-",15:"CD-",20:"CD-",25:"CD-",30:"CD-",35:"CD-",40:"CD-",45:"CD-",50:"CD-",55:"CD-",60:"CD-",65:"CD-",70:"CD-",75:"CD-",80:"CD-",85:"CD-",90:"D+",95:"D",100:"D-"},
            90:{0:"D+",5:"D+",10:"D+",15:"D+",20:"D+",25:"D+",30:"D+",35:"D+",40:"D+",45:"D+",50:"D+",55:"D+",60:"D+",65:"D+",70:"D+",75:"D+",80:"D+",85:"D+",90:"D+",95:"D",100:"D-"},
            95:{0:"D",5:"D",10:"D",15:"D",20:"D",25:"D",30:"D",35:"D",40:"D",45:"D",50:"D",55:"D",60:"D",65:"D",70:"D",75:"D",80:"D",85:"D",90:"D",95:"D",100:"D"},
            100:{0:"D-",5:"D-",10:"D-",15:"D-",20:"D-",25:"D-",30:"D-",35:"D-",40:"D-",45:"D-",50:"D-",55:"D-",60:"D-",65:"D-",70:"D-",75:"D-",80:"D-",85:"D-",90:"D-",95:"D-",100:"D-"}
        }


        # =============================
        # 4–8 (UNCHANGED)
        # =============================
        if 'Prev_DPD' not in df.columns:
            df['Prev_DPD'] = 0

        df['Prev_Band'] = df['Prev_DPD'].apply(dpd_to_band)
        df['Curr_Band'] = df['Days Past Due'].apply(dpd_to_band)

        def get_rating(prev_band, curr_band):
            try:
                return matrix[prev_band][curr_band]
            except:
                return None

        df['Updated_Rating'] = df.apply(
            lambda x: get_rating(x['Prev_Band'], x['Curr_Band']),
            axis=1
        )

        df['Rating_Changed'] = df['Updated_Rating'] != df['INTERNAL RATING']

        rating_order = [
            "A+","A","A-","AB+","AB","AB-",
            "B+","B","B-","BC+","BC","BC-",
            "C+","C","C-","CD+","CD","CD-",
            "D+","D","D-"
        ]

        def classify(old, new):
            if old == new:
                return "No Change"
            if old in rating_order and new in rating_order:
                return "Upgrade" if rating_order.index(new) < rating_order.index(old) else "Downgrade"
            return "Changed"

        df['Migration_Type'] = df.apply(
            lambda x: classify(x['INTERNAL RATING'], x['Updated_Rating']),
            axis=1
        )

        summary = df['Migration_Type'].value_counts().reset_index()
        summary.columns = ['Migration_Type', 'Count']

        output_file = "credit_migration_output.xlsx"

        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name="Detailed", index=False)
            summary.to_excel(writer, sheet_name="Summary", index=False)

        # ----------------------------
        # ✅ DISPLAY RESULTS
        # ----------------------------
        st.success("✅ AUTOMATION COMPLETE")

        st.subheader("📊 Summary")
        st.dataframe(summary)

        st.subheader("🔍 Detailed Output")
        st.dataframe(df)

        # Download
        with open(output_file, "rb") as f:
            st.download_button(
                "⬇ Download Output File",
                f,
                file_name=output_file
            )






if st.session_state.page == "home":
    home_page()

elif st.session_state.page == "migration":
    credit_migration_dashboard()

elif st.session_state.page == "scoring":
    automated_credit_scoring()

     

