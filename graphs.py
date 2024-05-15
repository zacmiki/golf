# Histogram of the last 100 Rounds ------------------------------

def histo_100(dff):
	import matplotlib.pyplot as plt
	import streamlit as st
	import pandas as pd
	
	df = pd.DataFrame(dff)
	
	# Assuming df is your pandas DataFrame
	# Create a figure and axis object
	
	fig, ax = plt.subplots()
	
	# Calculate the maximum value of df['AGS']
	max_value = df['AGS'].max()
	
	# Create a histogram with fixed range bins
	ax.hist(df['AGS'], bins=range(70, int(max_value) + 15, 4), edgecolor='black', alpha=0.5)
	
	# Add labels and title
	ax.set_xlabel('Strokes per Round')
	ax.set_ylabel('Frequency')
	ax.set_title('Strokes per round in the Last 100 FIG Tournaments')
	
	# Show the grid
	ax.grid(True)
	
	# Show both major and minor ticks
	ax.minorticks_on()
	
	# Customize grid for minor ticks only on the y-axis
	ax.grid(True, which='minor', axis='y', linestyle='--', color='red', linewidth=0.2)
	
	# Display the plot using Streamlit
	st.pyplot(fig)
	
	
	
# Plot the last 100 Results ------------------------
	 
def plot_last_100_results(dff):
	import matplotlib.pyplot as plt
	import streamlit as st
	import pandas as pd
	
	df = pd.DataFrame(dff)
	fig, ax = plt.subplots(figsize=(12, 7))
	
	reversed_index = df.index[::-1]
	ax.plot(df['Date_String'][::-1], df['Index Nuovo'][::-1], linestyle = '-', marker = 'o', color = 'purple', markersize = 8)
	#ax.plot(df["Data"], df["Index Nuovo"], linestyle="-", marker="o")
	
	ax.set_title("EGA Handicap vs Date for last 100 Rounds", fontsize=16)
	
	ax.set_ylabel("EGA", fontsize=16)
	ax.tick_params(axis="x", rotation=45)
	ax.grid(True)
	
	# Add minor ticks drawn in thin red dotted lines
	ax.grid(which="minor", linestyle=":", linewidth=0.2, color="red")
	
	#Set Special ticks for allocating the Strings
	ax.set_xticks(range(0, len(df['Date_String'][::-1]), 6))
	ax.set_xticklabels(df['Date_String'][::-1].iloc[::6])
	
	
	plt.tight_layout()
	st.pyplot(fig)