# בתוך הקובץ app.py, תחת tab_info (לשונית פרשנות חכמה):

with tab_info:
    st.subheader("💡 ניתוח טכני משולב")
    
    # יצירת שתי עמודות לפרשנות
    col_signals, col_levels = st.columns(2)
    
    with col_signals:
        st.markdown("### איתותי אינדיקטורים")
        explanations = generate_explanations(df, periods)
        for exp in explanations:
            st.info(exp) # מציג כל הסבר בתיבה כחולה נעימה לעין

    with col_levels:
        st.markdown("### רמות מחיר ודוחות")
        st.write(f"📅 **תאריך דוחות:** {next_earnings}")
        st.markdown("---")
        for lvl in levels:
            st.success(lvl) # מציג תמיכה והתנגדות בתיבה ירוקה
            
    # הוספת ציון כללי בתחתית הפרשנות
    score, rec, color = calculate_final_score(last_row, periods)
    st.markdown(f"""
    <div style="background-color:{color}; padding:20px; border-radius:15px; text-align:center; color:white;">
        <h2 style="color:white;">שורה תחתונה: {rec}</h2>
        <p style="font-size:20px;">ציון משוקלל: {score}/100</p>
    </div>
    """, unsafe_allow_html=True)
