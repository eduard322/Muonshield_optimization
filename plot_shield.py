

def plot_frame(frame, params):
    SKIPPING_STEP = 8
    PARAM_LENGTH = 56
    len_mask = [i for i in range(0, SKIPPING_STEP, 1)]
    f_l_mask = [i for i in range(SKIPPING_STEP, PARAM_LENGTH, 6)]
    f_r_mask = [i for i in range(SKIPPING_STEP + 1, PARAM_LENGTH, 6)]
    h_l_mask = [i for i in range(SKIPPING_STEP + 2, PARAM_LENGTH, 6)]
    h_r_mask = [i for i in range(SKIPPING_STEP + 3, PARAM_LENGTH, 6)]
    g_l_mask = [i for i in range(SKIPPING_STEP + 4, PARAM_LENGTH, 6)]
    g_r_mask = [i for i in range(SKIPPING_STEP + 5, PARAM_LENGTH, 6)]

len(set(f_l_mask + f_r_mask + h_l_mask + h_r_mask + g_l_mask + g_r_mask))


    masks = [[i for i in range(0, SKIPPING_STEP, 1)]]
for ind in range(SKIPPING_STEP):
    masks.append([i for i in range(SKIPPING_STEP + ind, PARAM_LENGTH, 6)])

print(len(set(elem for mask in masks for elem in mask)))
titles = ["Length", "f_l", "f_r", "h_l", "h_r", "g_l", "g_r"]
    ax = fig.add_subplot(gs1[0])
    x_start = 0
    for index in range(SKIPPING_STEP):
        if index < 4:
            COLOR= ['b', 'b', 'g']
        else:
            COLOR= ['g', 'g', 'b']
        length = 2 * params[index]
        draw_magnet_x(x_start, length, params[SKIPPING_STEP+ index * 6:
                                              SKIPPING_STEP+ (index + 1) * 6], ax,COLOR)
        #plt.axvline(x=x_start)
        GAP = 20 if index == 0 else 10
        if index == 6:
            GAP=0
        x_start += length + GAP

    # Plot sensitive plane a set a limit of plot to see the whole range
    ax.axvline(x=2598.0 - MAGN_COORDS[0][0], ymin=200/1000, ymax=800/1000)
    #ax.set_xlim(0,2598.0 - MAGN_COORDS[0][0] + 200)
    # this range will plot just magnet
    ax.set_xlim(0,3600)
    ax.set_ylim(-500,500)
    ax.set_xlabel("Z, cm", fontsize=19)
    ax.set_ylabel("X, cm", fontsize=19)
    ax.tick_params(axis='both', labelsize=20)
