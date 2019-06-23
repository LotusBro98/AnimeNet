package com.example.face2anime;

import android.graphics.Bitmap;
import android.graphics.BlendMode;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.os.Build;
import android.view.MotionEvent;
import android.widget.ImageView;
import android.widget.TextView;

import androidx.annotation.RequiresApi;

public class Painter {
    private Bitmap head;
    private Bitmap eyes;
    private Bitmap hair;

    private ImageView headView;
    private ImageView eyesView;
    private ImageView hairView;

    private boolean drawing = false;
    private int layer;
    private boolean erase = false;
    private Color brushColor;

    private Canvas headCanvas;
    private Canvas eyesCanvas;
    private Canvas hairCanvas;

    private Paint headPaint;
    private Paint eyesPaint;
    private Paint hairPaint;

    private float xPrev = -1;
    private float yPrev = -1;

    private int[] colors;

    public Painter(ImageView headView, ImageView eyesView, ImageView hairView) {
        this.headView = headView;
        this.eyesView = eyesView;
        this.hairView = hairView;

//        headPaint = new Paint();
//        eyesPaint = new Paint();
//        hairPaint = new Paint();

        colors = new int[3];

//        headPaint.setBlendMode(BlendMode.SRC);
//        eyesPaint.setBlendMode(BlendMode.SRC);
//        hairPaint.setBlendMode(BlendMode.SRC);
    }

    public void setErase(boolean erase) {
        this.erase = erase;
    }

    public Bitmap getHead() {
        return head;
    }

    public Bitmap getEyes() {
        return eyes;
    }

    public Bitmap getHair() {
        return hair;
    }

    public void setHead(Bitmap head) {
        this.head = head;
        headCanvas = new Canvas(head);
        colors[0] = recalcLayerColor(0);
    }

    public void setEyes(Bitmap eyes) {
        this.eyes = eyes;
        eyesCanvas = new Canvas(eyes);
        colors[1] = recalcLayerColor(1);
    }

    public void setHair(Bitmap hair) {
        this.hair = hair;
        hairCanvas = new Canvas(hair);
        colors[2] = recalcLayerColor(2);
    }

    public void setLayer(int index)
    {
        this.layer = index;
    }

    private Bitmap getLayerBitmap(int layer)
    {
        switch (layer)
        {
            case 0:
                return head;
            case 1:
                return eyes;
            case 2:
                return hair;
            default:
                return null;
        }
    }

    public int getLayer()
    {
        return layer;
    }

    public int getLayerColor(int layer)
    {
        return colors[layer];
    }

    public void setLayerColor(int layer, int color)
    {
        colors[layer] = color;
        Bitmap image = getLayerBitmap(layer);

        int w = image.getWidth();
        int h = image.getHeight();

        for (int i = 0; i < h; i++) {
            for (int j = 0; j < w; j++) {
                int pixel = image.getPixel(j, i);
                if (Color.alpha(pixel) > 128) {
                    image.setPixel(j, i, color);
                }
            }
        }
    }

    public int recalcLayerColor(int layer)
    {
        Bitmap image = getLayerBitmap(layer);

        int w = image.getWidth();
        int h = image.getHeight();
        int sz = 0;

        float r = 0;
        float g = 0;
        float b = 0;

        for (int i = 0; i < h; i++) {
            for (int j = 0; j < w; j++) {
                int pixel = image.getPixel(j, i);
                if (Color.alpha(pixel) > 128) {
                    r += Color.red(pixel);
                    g += Color.green(pixel);
                    b += Color.blue(pixel);
                    sz += 1;
                }
            }
        }

        r = r / sz;
        g = g / sz;
        b = b / sz;

        return Color.argb(255, (int)r, (int)g, (int)b);
    }

    private void putColor(Bitmap bitmap, float x, float y, float radius, int color)
    {
        int i0 = (int) (y - radius - 1);
        int j0 = (int) (x - radius - 1);

        if (i0 < 0)
            i0 = 0;
        if (j0 < 0)
            j0 = 0;

        int imax = (int) (y + radius + 1);
        int jmax = (int) (x + radius + 1);

        if (imax > bitmap.getHeight())
            imax = bitmap.getHeight();
        if (jmax > bitmap.getWidth())
            jmax = bitmap.getWidth();

        for (int i = i0; i < imax; i++)
            for (int j = j0; j < jmax; j++)
            {
                float len2 = (i - y) * (i - y) + (j - x) * (j - x);
                if (len2 < radius*radius)
                {
                    bitmap.setPixel(j, i, color);
                }
            }
    }

    private void drawLine(Bitmap bitmap, float x0, float y0, float x1, float y1, float radius, int color)
    {
        float len = (float) Math.sqrt((x0 - x1) * (x0 - x1) + (y0 - y1) * (y0 - y1));
        for (int i = 0; i < len; i++)
            putColor(bitmap, x0 + (x1 - x0) * i / len, y0 + (y1 - y0) * i / len, radius, color);
    }

    public boolean onTouchEvent(MotionEvent event)
    {
        float x = event.getX();
        float y = event.getY();

        float w = hair.getWidth();
        float h = hair.getHeight();

        float W = hairView.getWidth();
        float H = hairView.getHeight();

        int[] viewCoords = new int[2];
        hairView.getLocationOnScreen(viewCoords);

        float x0 = viewCoords[0];
        float y0 = viewCoords[1] + (H - W * h / w) / 2;

        x = (x - x0) * w / W;
        y = (y - y0) * h / W;

        float radius = 10;

        int color = erase ? Color.argb(0, 255, 255, 255) : getLayerColor(layer);

        ImageView view = null;
        Bitmap bitmap = null;

        switch (layer)
        {
            case 0:
                view = headView;
                bitmap = head;
                break;
            case 1:
                view = eyesView;
                bitmap = eyes;
                break;
            case 2:
                view = hairView;
                bitmap = hair;
                break;
        }

        if (bitmap != null && view != null) {
            //headCanvas.drawCircle(x, y, radius, headPaint);
            if (xPrev == -1 && yPrev == -1)
                putColor(bitmap, x, y, radius, color);
            else
                drawLine(bitmap, xPrev, yPrev, x, y, radius, color);
            view.setImageBitmap(bitmap);
        }

        xPrev = x;
        yPrev = y;

        if (event.getAction() == MotionEvent.ACTION_UP) {
            xPrev = -1;
            yPrev = -1;
            return true;
        }

        return false;
    }
}
