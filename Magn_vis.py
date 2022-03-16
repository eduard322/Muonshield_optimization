import matplotlib.patches as patches
import matplotlib.gridspec as gridspec

class Shielddrawer:
	SKIPPING_STEP = 8
	PARAM_LENGTH = 56
	MAGN_COORDS = [
		    [-6994.0000,   -6542.0000],
		    [-6522.0000,   -6106.0000],
		    [-6096.0000,   -5682.0000],
		    [-5672.0000,   -5110.0000],
		    [-5100.0000,   -4604.0000],
		    [-4594.0000,   -3984.0000],
		    [-3974.0000,   -3490.0000],
		    [-3490.0000,   -3470.0000]]
	titles = ["Length", "f_l", "f_r", "h_l", "h_r", "g_l", "g_r"]
	def __init__(self, POINTS):
		self.masks = [[i for i in range(0, self.SKIPPING_STEP, 1)]]
		for ind in range(self.SKIPPING_STEP):
    			self.masks.append([i for i in range(self.SKIPPING_STEP + ind, self.PARAM_LENGTH, 6)])	
		self.params = POINTS
		len_mask = [i for i in range(0, self.SKIPPING_STEP, 1)]
		self.f_l_mask = [i for i in range(self.SKIPPING_STEP, self.PARAM_LENGTH, 6)]
		self.f_r_mask = [i for i in range(self.SKIPPING_STEP + 1, self.PARAM_LENGTH, 6)]
		self.h_l_mask = [i for i in range(self.SKIPPING_STEP + 2, self.PARAM_LENGTH, 6)]
		self.h_r_mask = [i for i in range(self.SKIPPING_STEP + 3, self.PARAM_LENGTH, 6)]
		self.g_l_mask = [i for i in range(self.SKIPPING_STEP + 4, self.PARAM_LENGTH, 6)]
		self.g_r_mask = [i for i in range(self.SKIPPING_STEP + 5, self.PARAM_LENGTH, 6)]


	def draw_trapezoid(self, x_start, length, y_params, color):
		x = [x_start, x_start + length, x_start + length, x_start] 
		return patches.Polygon(xy=list(zip(x, y_params)), facecolor=color, alpha=1)




	def draw_magnet_x(self, x_start, length, params, axes, COLOR):
		f_l, f_r, h_l, h_r, g_l, g_r = params
		y_params = [-(g_l + 2 * f_l), -(g_r + 2 * f_r), -f_r - g_r, -f_l - g_l]
		patch = self.	draw_trapezoid(x_start, length, y_params, COLOR[0])
		axes.add_patch(patch)
				   
		y_params = [f_l + g_l, f_r + g_r, 2 * f_r + g_r, 2 * f_l + g_l]
		patch = self.draw_trapezoid(x_start, length, y_params, COLOR[1])
		axes.add_patch(patch)                           

		y_params = [-f_l, -f_r, f_r, f_l]
		patch = self.draw_trapezoid(x_start, length, y_params, COLOR[2])
		axes.add_patch(patch)
	    
    
	def plot_frame(self, frame, fig, gs1):
		params = self.params
		ax = fig.add_subplot(gs1[0])
		x_start = 0
		for index in range(self.SKIPPING_STEP):
			if index < 4:
			    COLOR= ['b', 'b', 'g']
			else:
			    COLOR= ['g', 'g', 'b']
			length = 2 * params[index]
			self.draw_magnet_x(x_start, length, params[self.SKIPPING_STEP+ index * 6:
						              self.SKIPPING_STEP+ (index + 1) * 6], ax,COLOR)
			#plt.axvline(x=x_start)
			GAP = 20 if index == 0 else 10
			if index == 6:
			    GAP=0
			x_start += length + GAP

		# Plot sensitive plane a set a limit of plot to see the whole range
		ax.axvline(x=2598.0 - self.MAGN_COORDS[0][0], ymin=200/1000, ymax=800/1000)
		#ax.set_xlim(0,2598.0 - MAGN_COORDS[0][0] + 200)
		# this range will plot just magnet
		ax.set_xlim(0,3600)
		ax.set_ylim(-500,500)
		ax.set_xlabel("Z, cm", fontsize=19)
		ax.set_ylabel("X, cm", fontsize=19)
		ax.tick_params(axis='both', labelsize=20)
		ax.legend(title = "Magnet parameters:", labels = [str(params)])
