#!/usr/pubsw/bin/julia

# Find corresponding histo and blockface images to co-register

#                   photo 1                  photo 2                  photo 3                 photo 4
#            /----------------------\/----------------------\/----------------------\/----------------------\
#           .|  |  |  |  |  |  |  | .|  |  |  |  |  |  |  | .|  |  |  |  |  |  |  | *|  |  |  |  |  |  |  | .|
# slice:    .01 02 03 04 05 06 07 08.09 10 11 12 13 14 15 16.17 18 19 20 21 22 23 24*25 26 27 28 29 30 31 32.33 ...
# photo:    .01                     .02                     .03                     *04                     .05 ...
# comp:     .01 02 03 04 05 06 07 08.09 10 11 12 13 14 15 16.17 18 19 20 21 22 23 24*01 02 03 04 05 06 07 08.09 ...
# histo(2): .   01                                                                      02                      ...
#            \----------------------------------------------------------------------/\------------------------- ... ------/
#                                histo 1 from any compartment                               histo 2 from any compartment

using Printf

maclist = ("MR243", "MR256", "MF275", "MF278")

for mac in maclist
  if mac == "MR243"
    tracer = "LY"

    block_dsec = 8	    # Number of sections b/w consecutive blockface photos
    block_1    = 4759	  # Number of first blockface photo
    block_end  = 4922	  # Number of last blockface photo

    histo_comp = 18	    # Compartment number (1, ..., 24) of histo sections
    histo_1    = 1	    # Number of first histo section (within compartment)
    histo_end  = 73	    # Number of last histo section (within compartment)

# What's up with these 3 images? Ignoring for now: mr243LY_c18_s74[abc]DF.jp2
  elseif mac == "MR256"
    tracer = "LY"

    block_dsec = 1	    # Number of sections b/w consecutive blockface photos
    block_1    = 20194	# Number of first blockface photo
    block_end  = 21518	# Number of last blockface photo

    histo_comp = 2	    # Compartment number (1, ..., 24) of histo sections
    histo_1    = 1	    # Number of first histo section (within compartment)
    histo_end  = 39	    # Number of last histo section (within compartment)
  elseif mac == "MF275"
    tracer = "FR"

    block_dsec = 1	    # Number of sections b/w consecutive blockface photos
    block_1    = 58436	# Number of first blockface photo
    block_end  = 59539	# Number of last blockface photo

    histo_comp = 4	    # Compartment number (1, ..., 24) of histo sections
    histo_1    = 1	    # Number of first histo section (within compartment)
    histo_end  = 58	    # Number of last histo section (within compartment)
  elseif mac == "MF278"
    tracer = "LY"

    block_dsec = 1	    # Number of sections b/w consecutive blockface photos
    block_1    = 63514	# Number of first blockface photo
    block_end  = 64647	# Number of last blockface photo

    histo_comp = 2	    # Compartment number (1, ..., 24) of histo sections
    histo_1    = 1	    # Number of first histo section (within compartment)
    histo_end  = 60	    # Number of last histo section (within compartment)
  end

  # Section numbers corresponding to all blockface photos
  block_isec = [1 + k * block_dsec for k = 0 : (block_end - block_1)]

  # Section numbers corresponding to all histo sections
  histo_isec = [histo_comp + (k-1) * 24 for k = histo_1 : histo_end]

  for ihisto = histo_1 : histo_end
    histo_file =
      @sprintf "%s%s_c%02d_s%02dnDF.jp2" lowercase(mac) tracer histo_comp ihisto

    iblock = findmin(abs.(block_isec .- histo_isec[ihisto]))[2]

    block_file = @sprintf "Img%d.JPG" block_1 + iblock - 1

    println(histo_file * " " * block_file)
  end
end
