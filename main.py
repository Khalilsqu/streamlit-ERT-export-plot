import streamlit as st
# import io
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.tri import Triangulation
from scipy.ndimage import gaussian_filter
from io import BytesIO

import hmac


st.set_page_config(page_title="Page Title", layout="wide")

st.markdown("""
    <style>
        .reportview-container {
            margin-top: -2em;
        }
        #MainMenu {visibility: hidden;}
        .stDeployButton {display:none;}
        footer {visibility: hidden;}
        #stDecoration {display:none;}
    </style>
""", unsafe_allow_html=True)


def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.header("Password protected")
    st.write("Please enter the password to continue.")
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False


if not check_password():
    st.stop()  # Don't run the rest of the app.

if 'df' not in st.session_state:
    st.session_state.df = None

if "df_electrode_locations" not in st.session_state:
    st.session_state.df_electrode_locations = None


def main():
    st.title("National Rocks ERT Data Analysis")
    st.write("This is a web application to analyze ERT data built by National Rocks")
    st.write("Please upload an Excel file to analyze the data")
    st.write(
        "The Excel file should contain the following columns as the first three columns:")
    st.write("x, elevation, resistivity")

    # Upload Excel file through Streamlit's file uploader
    uploaded_file = st.file_uploader(
        "Choose an Excel file", type=["xlsx", "xls"])

    if uploaded_file is not None:
        st.toast('Excel file uploaded successfully', icon='😍')

        # Use Pandas to read the Excel file
        try:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
            st.session_state.df = df
            st.dataframe(df)  # Display the DataFrame in Streamlit

            column_to_check = 0  # Change this to the index of your desired column

            # Find the index where the values in the specified column start decreasing
            index_to_stop = (df.iloc[:, column_to_check].diff() < 0).idxmax()

            # Get the data until the index where it starts decreasing again
            filtered_data = df.iloc[:index_to_stop, :]

            # Extract relevant information
            spacing = filtered_data.iloc[1, 0] - filtered_data.iloc[0, 0]

            # Calculate actual points based on the first point and spacing
            first_point = 0
            num_points = len(filtered_data)
            actual_points = np.linspace(
                first_point, (num_points - 1) * spacing, num_points)

            # Calculate mean of the second column in filtered_data for two rolling rows
            rolling_mean = (
                filtered_data.iloc[:, 1] + filtered_data.iloc[:, 1].shift(-1)) / 2

            # Ensure actual_points and rolling_mean have the same length
            min_length = min(len(actual_points), len(rolling_mean))
            actual_points = actual_points[:min_length]
            rolling_mean = rolling_mean[:min_length]

            # Fill the last NaN value in rolling_mean with the previous value
            rolling_mean.iloc[-1] = rolling_mean.iloc[-2]

            result_df = pd.DataFrame(
                {'Actual Points': actual_points, 'Mean of Second Column': rolling_mean})

            # new_row = result_df.iloc[-1:].copy()
            # new_row['Actual Points'] += spacing

            # result_df = pd.concat([result_df, new_row], ignore_index=True)

            # new_row = result_df.iloc[-1:].copy()
            # new_row['Actual Points'] += spacing

            # result_df = pd.concat([result_df, new_row], ignore_index=True)

            st.session_state.df_electrode_locations = result_df
        except Exception as e:
            st.toast('Error: Please upload a valid Excel file', icon='🤯')
    else:
        st.info("Please upload an Excel file.")

    if st.session_state.df is not None:

        with st.expander("Plot settings"):
            with st.form(key='my_form', border=False):
                st.write("Please enter the parameters for the plots")

                # Add sliders with help text

                st.slider('Smoothing', 0.0, 20.0, 4.0, 0.1, key='smoothing',
                          help='Adjust the level of smoothing applied to the data.')

                st.divider()
                st.slider('Number of contours', 2, 30, 15, 1, key='number_of_contours',
                          help='Specify the number of contour lines to be displayed.')
                st.slider('Main contour line width', 0.1, 1.0, 0.5, 0.05,
                          key='main_contour_lw', help='Set the width of the main contour lines.')
                st.slider('Bold contour line width', 0.1, 2.0, 1.0, 0.05,
                          key='bold_contour_lw', help='Set the width of the bold contour lines.')
                st.slider('Font size contour label', 2, 20, 10, 1, key='fontsize_contour_label',
                          help='Adjust the font size of the contour labels.')

                st.slider('Skip contour label every nth contour', 1, 5, 1, 1, key='skip_contour_every_nth',
                          help='Specify the interval for skipping contour labels. This is useful when there are too many contour lines')
                st.slider('Contour bold every nth', 1, 10, 5, 1, key='contour_bold_every_nth',
                          help='Specify the interval for making contour lines bold.')

                color_map_mat = ['viridis', 'plasma', 'inferno', 'magma', 'cividis',
                                 'Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds',
                                 'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu',
                                 'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn',
                                 'binary', 'gist_yarg', 'gist_gray', 'gray', 'bone',
                                 'pink', 'spring', 'summer', 'autumn', 'winter', 'cool',
                                 'Wistia', 'hot', 'afmhot', 'gist_heat', 'copper',
                                 'twilight', 'twilight_shifted', 'hsv',
                                 'ocean', 'gist_earth', 'terrain',
                                 'gist_stern', 'gnuplot', 'gnuplot2', 'CMRmap',
                                 'cubehelix', 'brg', 'gist_rainbow', 'rainbow', 'jet',
                                 'turbo', 'nipy_spectral', 'gist_ncar',
                                 ]

                # Add help text to the selectbox
                st.selectbox('Color map', color_map_mat, index=color_map_mat.index(
                    'rainbow'), key='color_map', help='Choose a color map for the plot.')

                st.link_button(
                    'Color map reference', 'https://matplotlib.org/stable/users/explain/colors/colormaps.html')

                # Add help text to the checkbox
                st.checkbox('Plot aspect ratio equal', value=True,
                            help='Check to make the plot aspect ratio equal so that one unit on the x-axis is equal to one unit on the y-axis', key='aspect_ratio_equal')

                st.divider()

                col1_width, col2_height, dpi = st.columns(3)

                with col1_width:
                    st.number_input(
                        'Figure width (inches)',
                        1,
                        100,
                        50,
                        1,
                        key='figure_width_inches',
                        help="Specify the width of the figure in inches. This is useful when the figure is too small or too large."
                        "Increase the the width if the length of the x-axis is too large."
                        "Decrease the width if the length of the x-axis is too small."
                    )

                with col2_height:
                    st.number_input(
                        'Figure height (inches)',
                        1,
                        100,
                        15,
                        1,
                        key='figure_height_inches',
                        help="Specify the height of the figure in inches. This is useful when the figure is too small or too large."
                        "Increase the the height if the length of the y-axis is too large."
                        "Decrease the height if the length of the y-axis is too small."
                    )

                with dpi:
                    st.number_input(
                        'Figure dpi',
                        50,
                        1000,
                        300,
                        130,
                        key='figure_dpi',
                        help="Specify the resolution of the figure. This is useful when the figure is too small or too large."
                    )
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.number_input(
                        'Electrode marker size', 1, 40, 4, 1, key='electrode_marker_size',
                        help="Specify the size of the electrode markers."
                    )
                with col2:
                    st.number_input(
                        "Tick label font size", 1, 40, 10, 1, key='tick_label_font_size',
                        help="Specify the font size of the tick labels."
                    )

                with col3:
                    st.number_input(
                        "Axis label font size", 1, 60, 14, 1, key='axis_label_font_size',
                        help="Specify the font size of the axis labels."
                    )

                st.divider()

                col1_xtick_number_bins, col2_ytick_number_bins = st.columns(
                    2)

                with col1_xtick_number_bins:
                    st.number_input(
                        "Number of x tick bins", 1, 100, 10, 1, key='x_tick_step_size',
                        help="Specify the number of bins for the x-axis."
                    )

                with col2_ytick_number_bins:
                    st.number_input(
                        "Number of y tick bins", 1, 100, 10, 1, key='y_tick_step_size',
                        help="Specify the number of bins for the y-axis."
                    )

                st.checkbox(
                    'Show grids', value=False, key='show_grids',
                    help="Check to show grids on the plot."
                )

                submit_button = st.form_submit_button(label='Apply changes')

        st.title("Data plots")

        data = st.session_state.df.to_numpy()

        data[:, 2] = gaussian_filter(
            data[:, 2], sigma=st.session_state.smoothing)

        x = data[:, 0]
        z = data[:, 1]
        rho = data[:, 2]

        clevels = np.logspace(np.log10(np.min(rho)),
                              np.log10(np.max(rho)),
                              num=st.session_state.number_of_contours, base=10)

        triang = Triangulation(x, z)

        def apply_mask(triang, alpha=0.4):
            # Mask triangles with sidelength bigger some alpha
            triangles = triang.triangles
            # Mask off unwanted triangles.
            xtri = x[triangles] - np.roll(x[triangles], 1, axis=1)
            ytri = z[triangles] - np.roll(z[triangles], 1, axis=1)
            maxi = np.max(np.sqrt(xtri**2 + ytri**2), axis=1)
            # apply masking
            triang.set_mask(maxi > alpha)

        apply_mask(triang, alpha=10)

        fig, ax = plt.subplots(
            facecolor='white', edgecolor='white',
            figsize=(st.session_state['figure_width_inches'],
                     st.session_state['figure_height_inches']),
            dpi=st.session_state['figure_dpi']
        )

        # Basic contour lines
        cs = ax.tricontour(triang, rho, levels=clevels,
                           colors='k',
                           linewidths=st.session_state.main_contour_lw,
                           )

        # Create labels for each contour line
        labels = [str(level) for level in cs.levels]

        # Label every other level using strings
        clabels = ax.clabel(
            cs, cs.levels[::st.session_state.skip_contour_every_nth], inline=True, fmt='%0.0f', colors='k',
            fontsize=st.session_state.fontsize_contour_label, use_clabeltext=True
        )

        # Make every fifth contour line and label bold
        for i, (clabel, contour_line) in enumerate(zip(clabels, cs.collections)):
            if (i + 1) % st.session_state.contour_bold_every_nth == 0:
                clabel.set_fontweight('bold')
                contour_line.set_linewidth(st.session_state.bold_contour_lw)

        # Filled contour plot
        cc = ax.tricontourf(triang, rho, levels=clevels, cmap=st.session_state.color_map,
                            norm=matplotlib.colors.LogNorm(vmin=rho.min(), vmax=rho.max()))

        ax.scatter(st.session_state.df_electrode_locations.iloc[:, 0],
                   st.session_state.df_electrode_locations.iloc[:, 1],
                   marker="v",
                   color='r',
                   s=st.session_state.electrode_marker_size,
                   )

        if st.session_state.aspect_ratio_equal:
            ax.set_aspect(
                aspect='equal', adjustable='box')

        ax.set_xlabel('Distance (m)',
                      fontsize=st.session_state.axis_label_font_size
                      )
        ax.set_ylabel('Elevation (m)',
                      fontsize=st.session_state.axis_label_font_size
                      )

        # Limit x and y axes to range to fit data
        x_range = x.max() - x.min()
        y_range = max(triang.y) - min(triang.y)
        ax.set_xlim([x.min() - 0.01 * x_range, x.max() + 0.01 * x_range])
        ax.set_ylim([min(triang.y) - 0.1 * y_range,
                    max(triang.y) + 0.2 * y_range])

        ax.tick_params(axis='both', which='major',
                       labelsize=st.session_state.tick_label_font_size)
        ax.tick_params(axis='both', which='minor',
                       labelsize=st.session_state.tick_label_font_size)

        ax.set_title(
            f'ERT Data for {uploaded_file.name.split(".")[0]}',
            fontsize=st.session_state.axis_label_font_size+2
        )

        # locator_params
        ax.locator_params(axis='x', nbins=st.session_state.x_tick_step_size)
        ax.locator_params(axis='y', nbins=st.session_state.y_tick_step_size)

        if st.session_state.show_grids:
            ax.grid()

        # Add colorbar
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="1%", pad=0.05)
        cbar = fig.colorbar(cc, cax=cax, format="%.0f")

        # ticks = [10**i for i in range(int(np.floor(np.log10(rho.min()))),
        #                               int(np.ceil(np.log10(rho.max()))), 1)]
        # cbar.set_ticks(ticks)
        # cbar.set_ticklabels(["$10^{%d}$" % np.log10(tick) for tick in ticks])
        cbar.set_label('Resistivity (Ω.m)',
                       fontsize=st.session_state.axis_label_font_size)
        cbar.ax.tick_params(labelsize=st.session_state.tick_label_font_size)

        # Define file formats and their properties
        file_formats = {
            "png": {"label": "Download Plot as PNG", "mime": 'image/png'},
            "pdf": {"label": "Download Plot as PDF", "mime": 'application/pdf'},
            "svg": {"label": "Download Plot as SVG", "mime": 'image/svg+xml'},
        }

        # Add selectbox for choosing the file format
        selected_format = st.selectbox(
            "Select file format:",
            list(file_formats.keys()),
            index=2,
            key='selected_format'
        )

        image_bytes = BytesIO()

        # Save plot to BytesIO object based on selected format
        fig.savefig(image_bytes, format=selected_format,
                    bbox_inches='tight', pad_inches=0.2, dpi=300
                    )
        image_bytes.seek(0)

        # Get file format properties based on selected format
        format_properties = file_formats[selected_format]

        # Add download button for the selected format
        st.download_button(
            label=format_properties["label"],
            data=image_bytes,
            file_name=f"{uploaded_file.name.split('.')[0]}.{selected_format}",
            mime=format_properties["mime"],
            key=f'download_button_{selected_format}'
        )

        st.pyplot(fig,
                  clear_figure=True,
                  bbox_inches='tight',
                  pad_inches=0.2,
                  use_container_width=True
                  )


if __name__ == "__main__":
    main()
