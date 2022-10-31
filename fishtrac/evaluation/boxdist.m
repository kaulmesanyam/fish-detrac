function dist=boxdist(x1,y1,w1,h1,x2,y2,w2,h2)    % compute intersection over union of two bboxes% % (C) Anton Andriyenko, 2012%% The code may be used free of charge for non-commercial and% educational purposes, the only requirement is that this text is% preserved within the derivative work. For any other purpose you% must contact the authors for permission. This code may not be% redistributed without written permission from the authors.     centerToConer = sqrt((w1*w1)/4 + (h1*h1)/4);    distX1 = x1+w1/2;    distX2 = x2+w2/2;    distY1 = y1+h1/2;    distY2 = y2+h2/2;    centerToCenter = sqrt((distX1-distX2)*(distX1-distX2)+(distY1-distY2)*(distY1-distY2));      iou=boxiou(x1,y1,w1,h1,x2,y2,w2,h2);          dist = centerToCenter/centerToConer;    if dist < 2            %disp(dist);      %disp(iou);    endend